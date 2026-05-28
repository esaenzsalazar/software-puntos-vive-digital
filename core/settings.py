"""
Django settings for Puntos Vive Digital project.
Configuration for the PVD management system - Contract CD-224-2026
Alcaldía de Bugalagrande - Valle del Cauca, Colombia
"""
from pathlib import Path
from dotenv import load_dotenv
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file for security
load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
# In production, set DJANGO_SECRET_KEY environment variable
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-g9@zgxyl-bfe0qrc9h8@$=d09ldfo7+oygr6q&=ykp=y2xzqb)')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

# Allowed hosts configuration with fallback for development
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost,testserver').split(',')
ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS]

# Add wildcard for development if not present (remove in production)
if '*' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('*')

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
    'http://localhost:8000',
    'http://127.0.0.1',
    'http://127.0.0.1:8000',
]
_extra_origins = os.getenv('CSRF_TRUSTED_ORIGINS', '')
if _extra_origins:
    CSRF_TRUSTED_ORIGINS.extend([o.strip() for o in _extra_origins.split(',')])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Local apps
    'modulo_puntos.apps.ModuloPuntosConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

# Template configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Custom context processor for PVD navigation
                'modulo_puntos.context_processors.pvd_navigation',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database configuration - MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'modeladobd'),
        'USER': os.getenv('DB_USER', 'avnadmin'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'mysql-3bb67bf0-alcaldiaesteban-d1bc.k.aivencloud.com'),
        'PORT': os.getenv('DB_PORT', '27827'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'es-co'  # Spanish (Colombia)
TIME_ZONE = 'America/Bogota'  # Colombia timezone
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files (user uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Authentication configuration
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
