from pathlib import Path
import os
import sys
import environ

# Load environment variables from .env file
env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent

# Add the project root to Python path so 'lib' module can be found
sys.path.insert(0, str(BASE_DIR))

# Explicitly load .env from the project root
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = env('SECRET_KEY', default='your-secret-key')

DEBUG = env.bool('DEBUG', default=True)

ALLOWED_HOSTS = ['*']

# Add CSRF trusted origins for production
CSRF_TRUSTED_ORIGINS = [
    'https://www.babelscrib.com',
    'https://dev.babelscrib.com',
    'https://babelscrib.com',
    'https://*.babelscrib.com',  # For any subdomain
]

# If you have additional domains, add them from environment variables
if env('CSRF_TRUSTED_ORIGINS', default=''):
    additional_origins = env.list('CSRF_TRUSTED_ORIGINS')
    CSRF_TRUSTED_ORIGINS.extend(additional_origins)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Required for allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.microsoft',
    'upload',  # Your upload app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add WhiteNoise for static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # Add locale middleware for i18n
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Required for allauth
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Additional Azure-specific settings for proper HTTPS handling
if not DEBUG:
    # Ensure Django trusts the X-Forwarded-Proto header from Azure
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True

ROOT_URLCONF = 'api.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'upload/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',  # Add i18n context processor
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'api.wsgi.application'
ASGI_APPLICATION = 'api.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

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

LANGUAGE_CODE = 'en'  # English as default
TIME_ZONE = 'UTC'
USE_I18N = False  # Temporarily disable i18n while we fix .mo files
USE_L10N = True
USE_TZ = True

# Internationalization settings
LANGUAGES = [
    ('en', 'English'),
    ('fr', 'Français'),
]

# Path where Django will look for translation files
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Azure Blob Storage settings
AZURE_STORAGE_CONNECTION_STRING = env('AZURE_STORAGE_CONNECTION_STRING', default='')
AZURE_STORAGE_CONTAINER_NAME_SOURCE = env('AZURE_STORAGE_CONTAINER_NAME_SOURCE', default='source')

# Azure Translation Service settings
AZURE_TRANSLATION_KEY = env('AZURE_TRANSLATION_KEY', default='')
AZURE_TRANSLATION_ENDPOINT = env('AZURE_TRANSLATION_ENDPOINT', default='')
AZURE_TRANSLATION_SOURCE_URI = env('AZURE_TRANSLATION_SOURCE_URI', default='')
AZURE_TRANSLATION_TARGET_URI = env('AZURE_TRANSLATION_TARGET_URI', default='')

# Microsoft Authentication settings
SITE_ID = 1

# Force HTTPS for OAuth redirects in production
if not DEBUG:
    # This ensures that allauth generates HTTPS URLs for OAuth redirects
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
else:
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http'

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Microsoft OAuth settings - Using database SocialApp instead of settings
# SOCIALACCOUNT_PROVIDERS configuration removed to avoid conflicts with SocialApp

# Allauth settings
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_AUTO_SIGNUP = True

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'upload.views': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Auto-log environment variables in debug mode
if DEBUG and env.bool('DJANGO_LOG_ENV_VARS', default=False):
    import logging
    
    # Configure logging first to ensure handlers are available
    import logging.config
    logging.config.dictConfig(LOGGING)
    
    logger = logging.getLogger(__name__)
    logger.info("=== STARTUP ENVIRONMENT VARIABLES ===")
    
    for key, value in sorted(os.environ.items()):
        # Mask sensitive values
        if any(sensitive in key.upper() for sensitive in ['SECRET', 'KEY', 'PASSWORD', 'TOKEN']):
            masked_value = '*' * min(len(value), 8) if value else 'None'
            display_value = masked_value
        else:
            display_value = value
        
        logger.info(f"ENV: {key}={display_value}")
    
    logger.info("=== END STARTUP ENVIRONMENT VARIABLES ===")

# Production Security Settings
if not DEBUG:
    # Restrict ALLOWED_HOSTS in production
    ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['dev.babelscrib.com', 'babelscrib.com', 'www.babelscrib.com'])
    
    # Trust proxy headers for HTTPS (Critical for Azure Container Apps/App Service)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # Force HTTPS for all URLs (this ensures OAuth redirects use HTTPS)
    SECURE_SSL_REDIRECT = True
    
    # Security headers
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    
    # Session security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CSRF security
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SAMESITE = 'Lax'
    
    USE_TZ = True
else:
    # For development, ensure we can test with http://localhost
    SECURE_SSL_REDIRECT = False
    SECURE_PROXY_SSL_HEADER = None

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# WhiteNoise configuration for serving static files in production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Optional: Set max age for static files caching (1 year)
WHITENOISE_MAX_AGE = 31536000

# Optional: Skip compression for certain file types if needed
# WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz', 'br']