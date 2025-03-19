from django.urls import path
from .views import show_upload_page, save_file, get_files, download, remove_file, get_system_stats

urlpatterns = [
    path('', show_upload_page, name='upload_page'),
    path('upload/', save_file, name='save_file'),
    path('files/', get_files, name='get_files'),
    path('download/<str:file_name>/', download, name='download'),  # Updated endpoint
    path('delete/<str:file_name>/', remove_file, name='remove_file'),
    path('stats/', get_system_stats, name='get_system_stats'),
]