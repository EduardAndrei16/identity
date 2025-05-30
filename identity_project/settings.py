"""
Django settings for identity_project project.
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-ih-tqopd=d^wq9^(o52*y^iyroq!uxrgado@!vhb@1u-chb$pa'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*', 'https://identity-me30.onrender.com', 'identity-me30.onrender.com']

# Application definition
INSTALLED_APPS = [
    'main',
    'okta_oauth2.apps.OktaOauth2Config',  
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# Authentication backends - specify the order
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'okta_oauth2.backend.OktaBackend',
]

# Okta Configuration
OKTA_AUTH = {
    "ORG_URL": "https://booking.okta.com/",
    "ISSUER": "https://booking.okta.com/oauth2/default",
    "CLIENT_ID": "0oanpf8ya7UtbJLwM417",
    "CLIENT_SECRET": "H-4noxdoNh3LoJXDFVVZH93LbpaG1q91lPr2slZyQemgR3Zgg7ABpEzoLuyifEVn",
    "SCOPES": "openid profile email offline_access",
    "REDIRECT_URI": "http://127.0.0.1:8000/oauth2/callback/",
    "LOGIN_REDIRECT_URL": "/",
    "CACHE_PREFIX": "okta",
    "CACHE_ALIAS": "default",
    "PUBLIC_NAMED_URLS": (),
    "PUBLIC_URLS": (),
    "USE_USERNAME": False,
}

# Simplified Okta settings for direct access in templates and views
OKTA_BASE_URL = 'https://booking.okta.com'
OKTA_ISSUER = 'https://booking.okta.com/oauth2/default'
OKTA_CLIENT_ID = '0oanpf8ya7UtbJLwM417'
OKTA_CLIENT_SECRET = 'H-4noxdoNh3LoJXDFVVZH93LbpaG1q91lPr2slZyQemgR3Zgg7ABpEzoLuyifEVn'
OKTA_REDIRECT_URI = 'http://127.0.0.1:8000/oauth2/callback/'

# Login/logout URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'main.middleware.OktaAuthMiddleware',
]

ROOT_URLCONF = 'identity_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'main' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'identity_project.wsgi.application'

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

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

# Default primary key field type
# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
