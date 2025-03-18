from django.contrib import admin
from .models import FileMetadata, ChunkMetadata, NodeMetadata

# FileMetadata model admin configuration
@admin.register(FileMetadata)
class FileMetadataAdmin(admin.ModelAdmin):
    list_display = ('filename', 'file_size', 'created_at', 'chunk_count')
    search_fields = ('filename', 'file_hash')
    readonly_fields = ('file_hash', 'created_at', 'updated_at')

# NodeMetadata model admin configuration
@admin.register(NodeMetadata)
class NodeMetadataAdmin(admin.ModelAdmin):
    list_display = ('node_id', 'status', 'current_load', 'last_heartbeat')
    list_filter = ('status',)
    readonly_fields = ('created_at', 'updated_at')

# ChunkMetadata model admin configuration
@admin.register(ChunkMetadata)
class ChunkMetadataAdmin(admin.ModelAdmin):
    list_display = ('file', 'chunk_index', 'node_id', 'chunk_size')
    list_filter = ('node_id',)
    search_fields = ('file__filename', 'chunk_hash')
    readonly_fields = ('created_at',)