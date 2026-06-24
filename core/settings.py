"""
Django settings for Puntos Vive Digital project.
Contract CD-224-2026 — Alcaldía de Bugalagrande, Valle del Cauca, Colombia

Comportamiento por entorno:
  Desarrollo  → DJANGO_DEBUG=True  (por defecto, sin cambios)
  Producción  → DJANGO_DEBUG=False + variables de entorno completas en .env
"""
from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')

# ── SEGURIDAD ──────────────────────────────────────────────────────────────────

DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

_secret_fallback = 'django-insecure-g9@zgxyl-bfe0qrc9h8@$=d09ldfo7+oygr6q&=ykp=y2xzqb)' if DEBUG else None
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', _secret_fallback)
if not SECRET_KEY:
    raise RuntimeError('DJANGO_SECRET_KEY no está configurada. Define esta variable de entorno en producción.')

# En desarrollo acepta cualquier host; en producción SOLO el dominio real.
if DEBUG:
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = [
        h.strip()
        for h in os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')
        if h.strip()
    ]

# ── CSRF ───────────────────────────────────────────────────────────────────────

CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
    'http://localhost:8000',
    'http://127.0.0.1',
    'http://127.0.0.1:8000',
]
_extra_origins = os.getenv('CSRF_TRUSTED_ORIGINS', '')
if _extra_origins:
    CSRF_TRUSTED_ORIGINS.extend([o.strip() for o in _extra_origins.split(',') if o.strip()])

# ── APLICACIONES ───────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'modulo_puntos.apps.ModuloPuntosConfig',
]

# ── MIDDLEWARE ─────────────────────────────────────────────────────────────────

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # sirve CSS/JS en producción sin Nginx extra
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

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
                'modulo_puntos.context_processors.pvd_navigation',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ── BASE DE DATOS ──────────────────────────────────────────────────────────────

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'modeladobd'),
        'USER': os.getenv('DB_USER', 'avnadmin'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'mysql-3bb67bf0-alcaldiaesteban-d1bc.k.aivencloud.com'),
        'PORT': os.getenv('DB_PORT', '27827'),
        # Aiven activa ANSI_QUOTES + ONLY_FULL_GROUP_BY a nivel de servidor;
        # init_command los sobreescribe por sesión con un modo compatible con Django.
        'OPTIONS': {
            'charset': 'utf8mb4',
            'connect_timeout': 30,
            'init_command': (
                "SET sql_mode='STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,"
                "NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'"
            ),
        },
        'CONN_MAX_AGE': 60,
        'CONN_HEALTH_CHECKS': True,
    }
}

# ── CACHÉ ──────────────────────────────────────────────────────────────────────
# En desarrollo: in-memory (por defecto de Django, no requiere nada extra).
# En producción: Redis — necesario para que el rate-limiting del login funcione
#                correctamente con múltiples workers de Gunicorn.

_REDIS_URL = os.getenv('REDIS_URL', '')
if _REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': _REDIS_URL,
            'OPTIONS': {
                'socket_connect_timeout': 5,
                'socket_timeout': 5,
            },
        }
    }

# ── CONTRASEÑAS ────────────────────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── INTERNACIONALIZACIÓN ───────────────────────────────────────────────────────

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# ── ARCHIVOS ESTÁTICOS ─────────────────────────────────────────────────────────

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'   # destino de `python manage.py collectstatic`

# En producción WhiteNoise comprime y añade hash de versión a los archivos.
STORAGES = {
    'staticfiles': {
        'BACKEND': (
            'django.contrib.staticfiles.storage.StaticFilesStorage'
            if DEBUG else
            'whitenoise.storage.CompressedManifestStaticFilesStorage'
        ),
    },
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
}

# ── ARCHIVOS DE MEDIA (imágenes de Evidencias) ─────────────────────────────────
# En desarrollo Django sirve /media/ automáticamente (ver core/urls.py).
# En producción Nginx debe servir /media/ apuntando a MEDIA_ROOT:
#   location /media/ { alias /ruta/al/proyecto/media/; }

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── AUTENTICACIÓN ──────────────────────────────────────────────────────────────

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/panel/'
LOGOUT_REDIRECT_URL = '/login/'

SESSION_COOKIE_AGE = 28800  # 8 horas

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── SEGURIDAD EN PRODUCCIÓN ────────────────────────────────────────────────────
# Se activan automáticamente cuando DEBUG=False.
# Requieren HTTPS funcionando; no activar antes de tener el certificado SSL.

SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000          # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'
    # Nginx hace el redirect 80→443; Django no debe hacer otro o habría bucle.
    SILENCED_SYSTEM_CHECKS = ['security.W008']

# ── LOGGING ────────────────────────────────────────────────────────────────────
# Desarrollo: solo consola.
# Producción: consola + archivo rotativo en logs/pvd.log (máx. 5 MB × 5 archivos).

_LOG_DIR = BASE_DIR / 'logs'
try:
    _LOG_DIR.mkdir(exist_ok=True)
except OSError:
    pass

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[{levelname}] {asctime} {module}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(_LOG_DIR / 'pvd.log'),
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'] if DEBUG else ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'] if DEBUG else ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'modulo_puntos': {
            'handlers': ['console'] if DEBUG else ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
