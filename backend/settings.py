

from pathlib import Path

from .config import settings

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = settings.secret_key.get_secret_value()

DEBUG = settings.debug

ALLOWED_HOSTS = [".render.com", "localhost", "127.0.0.1"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "myapi",
    "ninja_extra",
    "ninja_jwt",
    "django.contrib.postgres",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"


import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=settings.db_url.get_secret_value(),
        conn_max_age=600,
        ssl_require=True
    )
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = "static/"

from datetime import timedelta

SIMPLE_JWT= {
    'ACCESS_TOKEN_LIFETIME':timedelta(minutes= settings.jwt_access_lifetime_mins),
    'REFRESH_TOKEN_LIFETIME': timedelta(days= 1),
    'ROTATE_REFRESH_TOKENS': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,                   
    'AUTH_HEADER_TYPES': ('Bearer',),             
}

import os

os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key.get_secret_value()
os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint

# Rate Limiting 
NINJA_EXTRA = {
    "THROTTLE_CLASSES": [
        "ninja_extra.throttling.UserRateThrottle",
        "ninja_extra.throttling.AnonRateThrottle",
    ],
    "THROTTLE_RATES": {
        "user": "3/min",    # Logged-in users (Aman, your testers)
        "anon": "2/min",    # Strangers (if you had public endpoints)
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = settings.email_host
EMAIL_PORT = settings.email_port
EMAIL_USE_TLS = settings.email_use_tls
EMAIL_HOST_USER = settings.email_host_user
EMAIL_USE_SSL = False
EMAIL_HOST_PASSWORD = settings.email_host_password.get_secret_value()
EMAIL_TIMEOUT = 10
EMAIL_USE_SSL = False


CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Kolkata'