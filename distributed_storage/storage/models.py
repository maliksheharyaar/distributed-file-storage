from django.db import models
from django.utils import timezone

# FileMetadata model to store metadata about each file
class FileMetadata(models.Model):
    filename = models.CharField(max_length=255)
    version = models.IntegerField(default=1)  # New field for version control
    file_size = models.BigIntegerField()  # Compressed file size
    original_file_size = models.BigIntegerField(null=True, blank=True)  # Original file size
    file_hash = models.CharField(max_length=64)
    chunk_count = models.IntegerField()
    file_url = models.URLField()
    is_compressed = models.BooleanField(default=False)
    is_encrypted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.filename

# NodeMetadata model to store metadata about each node 
class NodeMetadata(models.Model):
    node_id = models.CharField(max_length=50, unique=True)
    endpoint_url = models.URLField()
    status = models.CharField(max_length=20, default='inactive')
    current_load = models.BigIntegerField(default=0)
    last_heartbeat = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.node_id} ({self.status})"

# ChunkMetadata model to store metadata about each chunk
class ChunkMetadata(models.Model):
    file = models.ForeignKey(FileMetadata, on_delete=models.CASCADE)
    chunk_index = models.IntegerField()
    chunk_hash = models.CharField(max_length=64)
    chunk_size = models.BigIntegerField()
    node_id = models.CharField(max_length=50)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('file', 'chunk_index', 'node_id')

    def __str__(self):
        return f"{self.file.filename} - Chunk {self.chunk_index} on {self.node_id}"
