import os
from pathlib import Path
from decouple import config
from datetime import timedelta
from celery.schedules import crontab

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-your-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'drf_spectacular',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',

    # Local apps
    'apps.accounts',
    'apps.attendance',
    'apps.leave',
    'apps.core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.AuditLogMiddleware',
]

ROOT_URLCONF = 'bb_eams.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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


WSGI_APPLICATION = 'bb_eams.wsgi.application'

# --- MongoDB Configuration ---

# First, get the credentials. They will be empty if not set in .env
MONGO_USER = config('MONGO_USER', default='')
MONGO_PASSWORD = config('MONGO_PASSWORD', default='')

# MongoDB Configuration
DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'NAME': config('MONGO_DB_NAME', default='bb_eams_db'),
        'ENFORCE_SCHEMA': False,
        'CLIENT': { 'host': config('MONGO_HOST', default='localhost') }
    }
}

# Conditionally add authentication details ONLY if a username and password are provided.
# This allows connecting to a local, unauthenticated DB without errors.
if MONGO_USER and MONGO_PASSWORD:
    DATABASES['default']['CLIENT']['username'] = MONGO_USER
    DATABASES['default']['CLIENT']['password'] = MONGO_PASSWORD
    DATABASES['default']['CLIENT']['authSource'] = config('MONGO_AUTH_SOURCE', default='admin')
    DATABASES['default']['CLIENT']['authMechanism'] = 'SCRAM-SHA-1'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
# drf-spectacular settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'BB EAMS API',
    'DESCRIPTION': 'API documentation for the Biometric-Based Employee Attendance Management System',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_SETTINGS': {
        'operationsSorter': 'alpha',
        'tagsSorter': 'alpha',
        'docExpansion': 'list',
    },
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# CORS settings
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000').split(',')
CORS_ALLOW_CREDENTIALS = True

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
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
TIME_ZONE = 'Africa/Addis_Ababa'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Celery Configuration
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'calculate-daily-attendance-every-night': {
        'task': 'apps.attendance.tasks.calculate_daily_attendance',
        'schedule': crontab(hour=1, minute=30),  # Runs daily at 1:30 AM
    },
    'sync-offline-attendance-every-5-minutes': {
        'task': 'apps.attendance.tasks.sync_offline_attendance',
        'schedule': timedelta(minutes=5),
    },
    'cleanup-old-records-weekly': {
        'task': 'apps.attendance.tasks.cleanup_old_records',
        'schedule': crontab(hour=3, minute=0, day_of_week='sunday'), # Runs every Sunday at 3:00 AM
    }
}

# Biometric Settings
BIOMETRIC_TEMPLATE_ENCRYPTION_KEY = config('BIOMETRIC_ENCRYPTION_KEY', default='')
MAX_BIOMETRIC_RETRIES = 3
ATTENDANCE_SYNC_INTERVAL = 300  # 5 minutes

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')


STATICFILES_DIRS = [os.path.join(BASE_DIR, 'bb_eams', 'static')]
os.makedirs(STATICFILES_DIRS[0], exist_ok=True)