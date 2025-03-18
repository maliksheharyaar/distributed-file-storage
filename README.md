# Distributed File Storage System

A distributed file storage system built with Django and MinIO, featuring file chunking, replication, and health monitoring.

## Features

- File upload with automatic chunking (5MB chunks)
- File replication across multiple storage nodes
- Health monitoring of storage nodes
- File integrity verification
- Modern web interface with real-time updates
- File search and management capabilities

## System Requirements

- Python 3.8+
- Docker
- Docker Compose
- pip (Python package manager)

## Project Setup

1. **Clone the Repository**
```bash
git clone [repository-url]
cd distributed-file-stoage-main
```

2. **Create Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip3 install django==5.1.5
pip3 install djangorestframework
pip3 install django-cors-headers
pip3 install boto3
```

4. **MinIO Setup**
```bash
cd distributed_storage
docker-compose up -d
```

5. **Database Setup**
```bash
python3 manage.py makemigrations storage
python3 manage.py migrate
```

## Configuration

The system uses two MinIO instances for distributed storage. Configuration is in `settings.py`:

```python
STORAGE_NODES = {
    'node1': {
        'endpoint_url': 'http://localhost:9010',
        'access_key': 'minioadmin',
        'secret_key': 'minioadmin',
        'bucket': 'file-storage'
    },
    'node2': {
        'endpoint_url': 'http://localhost:9020',
        'access_key': 'minioadmin2',
        'secret_key': 'minioadmin2',
        'bucket': 'file-storage'
    }
}
```

## Running the Application

```bash
python3 manage.py runserver
```

## Access Points

- Web Interface: `http://localhost:8000/storage/`
- MinIO Console 1: `http://localhost:9011` (admin/user&pass = minioadmin)
- MinIO Console 2: `http://localhost:9021` (admin/user&pass = minioadmin2)

## System Architecture

- **Frontend**: HTML/TailwindCSS
- **Backend**: Django/Django REST Framework
- **Storage**: MinIO (S3-compatible object storage)
- **Database**: SQLite (default)

## Features in Detail

1. **File Upload**
   - Automatic file chunking (5MB chunks)
   - Distributed storage across nodes
   - Chunk replication for redundancy

2. **Storage Management**
   - Node health monitoring
   - Load balancing
   - Automatic bucket creation

3. **File Operations**
   - Upload with progress tracking
   - Download with integrity verification
   - File deletion with cleanup
   - File listing and search

4. **System Monitoring**
   - Storage usage tracking
   - Node status monitoring
   - Chunk distribution visualization