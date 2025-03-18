from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from .models import FileMetadata, ChunkMetadata, NodeMetadata
import boto3
import hashlib
from django.conf import settings
import math
from django.utils import timezone
from concurrent.futures import ThreadPoolExecutor
from botocore.exceptions import ClientError
from django.urls import reverse

CHUNK_SIZE = 5 * 1024 * 1024  # 5MB chunks
REPLICATION_FACTOR = 2  # Number of copies to maintain

# Initialize storage nodes from settings
storage_nodes = {
    node_id: boto3.client(
        's3',
        endpoint_url=config['endpoint_url'],
        aws_access_key_id=config['access_key'],
        aws_secret_access_key=config['secret_key']
    )
    for node_id, config in settings.STORAGE_NODES.items()
}

# Ensure the bucket exists on the node
def ensure_bucket_exists(node_id):
    try:
        bucket_name = settings.STORAGE_NODES[node_id]['bucket']
        client = storage_nodes[node_id]
        
        try:
            client.head_bucket(Bucket=bucket_name)
        except ClientError:
            # Bucket doesn't exist, create it
            client.create_bucket(Bucket=bucket_name)
            
            # Configure bucket for public access
            client.put_bucket_policy(
                Bucket=bucket_name,
                Policy='''{
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "PublicRead",
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": ["s3:GetObject"],
                            "Resource": ["arn:aws:s3:::''' + bucket_name + '''/*"]
                        }
                    ]
                }'''
            )
        return True
    except Exception as e:
        print(f"Error ensuring bucket exists on node {node_id}: {str(e)}")
        return False

# Initialize buckets when module loads
def initialize_storage():
    for node_id in storage_nodes:
        ensure_bucket_exists(node_id)

# Initialize buckets when module loads
initialize_storage()

def check_node_health(node_id, client):
    try:
        # Check if node is accessible and bucket exists
        ensure_bucket_exists(node_id)
        
        # Update node metadata
        node = NodeMetadata.objects.get_or_create(node_id=node_id)[0]
        node.status = 'active'
        node.last_heartbeat = timezone.now()
        node.endpoint_url = settings.STORAGE_NODES[node_id]['endpoint_url']
        node.save()
        
        return True
    except Exception as e:
        print(f"Node {node_id} health check failed: {str(e)}")
        NodeMetadata.objects.filter(node_id=node_id).update(
            status='inactive',
            last_heartbeat=timezone.now()
        )
        return False

# Update the health of the nodes
def update_node_health():
    with ThreadPoolExecutor(max_workers=len(storage_nodes)) as executor:
        results = executor.map(
            lambda x: check_node_health(x[0], x[1]), 
            storage_nodes.items()
        )
    return list(results)

def get_least_loaded_nodes(count=REPLICATION_FACTOR):
    # Update node health first
    update_node_health()
    
    # Get active nodes sorted by load
    nodes = NodeMetadata.objects.filter(
        status='active'
    ).order_by('current_load')[:count]
    
    # Get the node IDs of the active nodes
    node_ids = [n.node_id for n in nodes]
    
    # If not enough active nodes, use available ones
    if len(node_ids) < count:
        available_nodes = list(storage_nodes.keys())
        node_ids.extend(
            [n for n in available_nodes if n not in node_ids][:count - len(node_ids)]
        )
    
    return node_ids[:count]

# Create chunks of the file
def create_chunks(file_content, chunk_size=CHUNK_SIZE):
    total_chunks = math.ceil(len(file_content) / chunk_size)
    chunks = []
    
    for i in range(total_chunks):
        start = i * chunk_size
        end = start + chunk_size
        chunk = file_content[start:end]
        chunk_hash = hashlib.sha256(chunk).hexdigest()
        chunks.append((chunk, chunk_hash))
    
    return chunks

# Save a file to the storage nodes
@csrf_protect
def save_file(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file found'}, status=400)

    uploaded_file = request.FILES['file']
    
    # Read the content once and store it in memory
    content = uploaded_file.read()
    file_hash = hashlib.sha256(content).hexdigest()

    # Check for duplicate file
    existing_file = FileMetadata.objects.filter(file_hash=file_hash).first()
    if existing_file:
        return JsonResponse({
            'message': 'File exists',
            'id': existing_file.id,
            'url': existing_file.file_url
        })

    chunks = create_chunks(content)
    target_nodes = get_least_loaded_nodes()
    
    try:
        # Ensure buckets exist
        for node_id in target_nodes:
            ensure_bucket_exists(node_id)

        # Store the complete file on the primary node
        primary_node = target_nodes[0]
        primary_client = storage_nodes[primary_node]
        bucket_name = settings.STORAGE_NODES[primary_node]['bucket']
        
        # Upload complete file using the content we already read
        primary_client.put_object(
            Bucket=bucket_name,
            Key=uploaded_file.name,
            Body=content
        )
        
        # Generate the correct URL for file access
        file_url = f"{settings.STORAGE_NODES[primary_node]['endpoint_url']}/{bucket_name}/{uploaded_file.name}"
        
        # Store file metadata
        file_metadata = FileMetadata.objects.create(
            filename=uploaded_file.name,
            file_size=len(content),  # Use the actual content length
            file_hash=file_hash,
            chunk_count=len(chunks),
            file_url=file_url
        )

        # Store chunks with replication
        for idx, (chunk_data, chunk_hash) in enumerate(chunks):
            chunk_name = f"{file_hash}_chunk_{idx}"
            
            # Store chunk on multiple nodes using put_object instead of upload_fileobj
            for node_id in target_nodes:
                storage_nodes[node_id].put_object(
                    Bucket=settings.STORAGE_NODES[node_id]['bucket'],
                    Key=chunk_name,
                    Body=chunk_data
                )
                
                # Store chunk metadata
                ChunkMetadata.objects.create(
                    file=file_metadata,
                    chunk_index=idx,
                    chunk_hash=chunk_hash,
                    node_id=node_id,
                    chunk_size=len(chunk_data)
                )

            # Update node load
            for node_id in target_nodes:
                node = NodeMetadata.objects.get_or_create(node_id=node_id)[0]
                node.current_load += len(chunk_data)
                node.save()

        return JsonResponse({
            'message': 'Upload success',
            'id': file_metadata.id,
            'url': file_url
        }, status=201)
        
    except Exception as e:
        return JsonResponse({'error': f'Upload failed: {str(e)}'}, status=500)

# Get all files from the database and return as JSON
@api_view(['GET'])
def get_files(request):
    try:
        files = FileMetadata.objects.all()
        file_list = [{
            'name': f.filename,
            'size': format_size(f.file_size),
            'url': f.file_url,
            'modified': f.created_at.strftime('%Y-%m-%d %H:%M'),
            'chunks': {
                'count': f.chunk_count,
                'size': format_size(CHUNK_SIZE),
                'replicas': REPLICATION_FACTOR
            }
        } for f in files]

        return Response({'files': file_list})
    except Exception as e:
        return Response({'error': str(e)}, status=500)

# Get the download URL for a file
@api_view(['GET'])
def get_download_url(request, file_name):
    try:
        file_metadata = FileMetadata.objects.get(filename=file_name)
        chunks = ChunkMetadata.objects.filter(file=file_metadata).order_by('chunk_index')
        
        # Verify file integrity
        for chunk in chunks:
            node_id = chunk.node_id
            chunk_name = f"{file_metadata.file_hash}_chunk_{chunk.chunk_index}"
            
            # Get chunk from storage
            response = storage_nodes[node_id].get_object(
                Bucket="file-storage",
                Key=chunk_name
            )
            
            chunk_data = response['Body'].read()
            chunk_hash = hashlib.sha256(chunk_data).hexdigest()
            
            # Verify chunk integrity
            if chunk_hash != chunk.chunk_hash:
                # Try to repair from replica
                for replica in chunks.filter(chunk_index=chunk.chunk_index).exclude(node_id=node_id):
                    response = storage_nodes[replica.node_id].get_object(
                        Bucket="file-storage",
                        Key=chunk_name
                    )
                    replica_data = response['Body'].read()
                    if hashlib.sha256(replica_data).hexdigest() == chunk.chunk_hash:
                        # Repair corrupted chunk
                        storage_nodes[node_id].put_object(
                            Bucket="file-storage",
                            Key=chunk_name,
                            Body=replica_data
                        )
                        break
                else:
                    return Response({'error': 'File corruption detected'}, status=500)

        return Response({'url': file_metadata.file_url})
    except FileMetadata.DoesNotExist:
        return Response({'error': 'File not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

# Remove a file from the database and all nodes 
@csrf_protect
@api_view(['DELETE'])
def remove_file(request, file_name):
    try:
        file_metadata = FileMetadata.objects.get(filename=file_name)
        chunks = ChunkMetadata.objects.filter(file=file_metadata)
        
        # Delete chunks from all nodes
        for chunk in chunks:
            chunk_name = f"{file_metadata.file_hash}_chunk_{chunk.chunk_index}"
            node_id = chunk.node_id
            
            try:
                storage_nodes[node_id].delete_object(
                    Bucket="file-storage",
                    Key=chunk_name
                )
                
                # Update node load
                node = NodeMetadata.objects.get(node_id=node_id)
                node.current_load = max(0, node.current_load - chunk.chunk_size)
                node.save()
                
            except Exception:
                pass  # Continue deletion even if a chunk is missing
        
        # Delete metadata
        chunks.delete()
        file_metadata.delete()
        
        return JsonResponse({'message': 'File deleted'})
    except FileMetadata.DoesNotExist:
        return JsonResponse({'error': 'File not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Format the size of the file
def format_size(bytes):
    if bytes == 0:
        return '0 B'
    sizes = ['B', 'KB', 'MB', 'GB']
    i = int(math.floor(math.log(bytes) / math.log(1024)))
    return f"{(bytes / math.pow(1024, i)):.1f} {sizes[i]}"

# Get the initial stats of the system
def get_initial_stats():
    try:
        total_files = FileMetadata.objects.count()
        nodes = NodeMetadata.objects.all()
        total_load = sum(node.current_load for node in nodes)
        active_nodes = sum(1 for node in nodes if node.status == 'active')
        
        return {
            'total_files': total_files,
            'storage_used': format_size(total_load),
            'active_nodes': active_nodes
        }
    except Exception as e:
        print(f"Error getting initial stats: {str(e)}")
        return {
            'total_files': 0,
            'storage_used': '0 B',
            'active_nodes': 0
        }

def prepare_file_list():
    """Prepare the initial file list with formatted data"""
    try:
        files = FileMetadata.objects.all()
        return [{
            'name': f.filename,
            'size': format_size(f.file_size),
            'url': f.file_url,
            'modified': f.created_at.strftime('%Y-%m-%d %H:%M'),
            'chunks': {
                'count': f.chunk_count,
                'size': format_size(CHUNK_SIZE),
                'replicas': REPLICATION_FACTOR
            }
        } for f in files]
    except Exception as e:
        print(f"Error preparing file list: {str(e)}")
        return []

# Get the endpoints for the frontend 
def get_endpoints():
    """Get all API endpoints for the frontend"""
    return {
        # Upload a file to the storage nodes
        'upload': reverse('save_file'),
        # Get all files from the database
        'files': reverse('get_files'),
        # Get the system stats
        'stats': reverse('get_system_stats'),
        # Remove a file from the database and all nodes
        'delete_base': reverse('remove_file', kwargs={'file_name': 'FILENAME'})
    }

# Show the upload page
def show_upload_page(request):
    """Render the upload page with initial data"""
    context = {
        'stats': get_initial_stats(),
        'initial_files': prepare_file_list(),
        'endpoints': get_endpoints(),
        'chunk_size': CHUNK_SIZE,
        'replication_factor': REPLICATION_FACTOR
    }
    return render(request, 'storage/upload.html', context)

# Get the system stats
@api_view(['GET'])
def get_system_stats(request):
    try:
        total_files = FileMetadata.objects.count()
        total_chunks = ChunkMetadata.objects.count()
        nodes = NodeMetadata.objects.all()
        total_load = sum(node.current_load for node in nodes)
        
        node_stats = [{
            'id': node.node_id,
            'load': format_size(node.current_load),
            'status': 'active',
            'chunks': ChunkMetadata.objects.filter(node_id=node.node_id).count()
        } for node in nodes]
        
        return Response({
            'total_files': total_files,
            'total_chunks': total_chunks,
            'total_storage': format_size(total_load),
            'replication_factor': REPLICATION_FACTOR,
            'nodes': node_stats
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)

