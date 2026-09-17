import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-sih26190-securedocs-secret-key-dev')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',

    # SecureDocs Local Apps
    'accounts.apps.AccountsConfig',
    'cases.apps.CasesConfig',
    'documents.apps.DocumentsConfig',
    'ledger.apps.LedgerConfig',
    'sync.apps.SyncConfig',
    'alerts.apps.AlertsConfig',
    'audit.apps.AuditConfig',
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

ROOT_URLCONF = 'securedocs.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'securedocs.wsgi.application'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

if os.getenv('POSTGRES_DB'):
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# REST Framework Configuration with QueryStringJWTAuthentication support
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'securedocs.authentication.QueryStringJWTAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'STATIC']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Master Key for Fernet Document Encryption (Stable deterministic key for dev restarts)
MASTER_KEY = os.getenv('MASTER_KEY', '4Vz7VpW3W8qL+mK7vQ8E9dF0G1H2I3J4K5L6M7N8O9P=')

# Anomaly Detection Settings
ANOMALY_SCAN_INTERVAL_SECONDS = int(os.getenv('ANOMALY_SCAN_INTERVAL_SECONDS', 120))

ANOMALY_RULES = {
    'BULK_DOWNLOAD': {
        'ENABLED': True,
        'THRESHOLD': int(os.getenv('BULK_DOWNLOAD_THRESHOLD', 5)),
        'WINDOW_MINUTES': int(os.getenv('BULK_DOWNLOAD_WINDOW_MINUTES', 10)),
    },
    'OFF_HOURS_ACCESS': {
        'ENABLED': True,
        'START_HOUR': os.getenv('ALLOWED_HOURS_START', '08:00'),
        'END_HOUR': os.getenv('ALLOWED_HOURS_END', '20:00'),
    },
    'UNAUTHORIZED_ATTEMPTS': {
        'ENABLED': True,
        'THRESHOLD': int(os.getenv('DENIED_THRESHOLD', 3)),
        'WINDOW_MINUTES': int(os.getenv('DENIED_WINDOW_MINUTES', 15)),
    },
    'FAILED_LOGIN_LOCKOUT': {
        'ENABLED': True,
        'MAX_FAILED_LOGINS': int(os.getenv('MAX_FAILED_LOGINS', 5)),
    },
    'DEDUP_MINUTES': int(os.getenv('ALERT_DEDUP_MINUTES', 30)),
}

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

CELERY_BEAT_SCHEDULE = {
    'scan-access-patterns-every-2-min': {
        'task': 'alerts.tasks.scan_access_patterns',
        'schedule': ANOMALY_SCAN_INTERVAL_SECONDS,
    },
}
