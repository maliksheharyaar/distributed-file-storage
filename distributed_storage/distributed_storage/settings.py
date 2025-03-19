"""
Django settings for distributed_storage project.

Generated by 'django-admin startproject' using Django 5.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-$cuzv9@4(ekfw)5iqrnb$nvg7ynvs8x0mg2pd^1bf#+h+=6(w6'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'storage',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'distributed_storage.urls'

TEMPLATES = [
    {
        
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "storage/templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'distributed_storage.wsgi.application'

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# MinIO Configuration
STORAGE_NODES = {
    'node1': {
        'endpoint_url': 'http://minio1:9000',
        'access_key': 'minioadmin',
        'secret_key': 'minioadmin',
        'bucket': 'file-storage'
    },
    'node2': {
        'endpoint_url': 'http://minio2:9000',
        'access_key': 'minioadmin2',
        'secret_key': 'minioadmin2',
        'bucket': 'file-storage'
    }
}

AWS_S3_ENDPOINT_URL = STORAGE_NODES['node1']['endpoint_url']  # Default node
AWS_ACCESS_KEY_ID = STORAGE_NODES['node1']['access_key']
AWS_SECRET_ACCESS_KEY = STORAGE_NODES['node1']['secret_key']
AWS_STORAGE_BUCKET_NAME = STORAGE_NODES['node1']['bucket']
AWS_S3_ADDRESSING_STYLE = "path"
AWS_S3_USE_SSL = False
AWS_DEFAULT_ACL = None
AWS_S3_VERIFY = False
AWS_S3_REGION_NAME = None

# MinIO Console URL (for browser access)
MINIO_CONSOLE_URL = "http://localhost:9001"  # Console endpoint

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# MinIO Instance Configurations
MINIO_INSTANCE_1_URL = "http://minio:9000"
MINIO_INSTANCE_1_ACCESS_KEY = "minioadmin"
MINIO_INSTANCE_1_SECRET_KEY = "minioadmin"

MINIO_INSTANCE_2_URL = "http://minio:9000"
MINIO_INSTANCE_2_ACCESS_KEY = "minioadmin"
MINIO_INSTANCE_2_SECRET_KEY = "minioadmin"

MINIO_BUCKET_NAME = "file-storage"
