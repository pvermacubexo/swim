"""
Django settings for SharkDeck project.

Generated by 'django-admin startproject' using Django 3.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
import os
from datetime import timedelta
from pathlib import Path

from django.contrib import messages

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_URL = '/static/'
BASE_DIR = Path(__file__).resolve().parent.parent
STATICFILES_DIRS = (
    os.path.join(PROJECT_DIR, 'static'),
)
SECRET_KEY = 'jd(2z+97zheo^z41l!u%z4$4of#8+!fept9m79z%0!g$hs-@&0'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition
AUTH_USER_MODEL = 'user.User'
INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'Appointment',
    'user',
    'InstructorDashboard',
    'StripePayment',
    'ContactUs',
    'django_seed',
    'app',
    'celery',
    'django_celery_results',
    'django_celery_beat',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
BASE_URL = "http://192.168.1.12:8000"
ROOT_URLCONF = 'SharkDeck.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
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

WSGI_APPLICATION = 'SharkDeck.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
#
# if os.environ.get('DATABASE_NAME'):
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.postgresql_psycopg2',
#             'NAME': os.environ.get('DATABASE_NAME'),
#             'USER': os.environ.get('DATABASE_USER'),
#             'PASSWORD': os.environ.get('DATABASE_PASSWORD'),
#             'HOST': os.environ.get('DATABASE_HOST'),
#             'PORT': os.environ.get('DATABASE_PORT', default='5432'),
#         }
#     }
# else:
# #
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'd6ecfhttf73ste',
#         'USER': 'nnrdlqzfkglpgg',
#         'PASSWORD': 'c2edb63965d64fa5a84b6574d74d0c7ea4c3dcf0f1207d6f358ff96b42dd1428',
#         'HOST': 'ec2-34-204-127-36.compute-1.amazonaws.com',
#         'PORT': '5432',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'd6ecfhttf73ste',
        'USER': 'nnrdlqzfkglpgg',
        'PASSWORD': 'c2edb63965d64fa5a84b6574d74d0c7ea4c3dcf0f1207d6f358ff96b42dd1428',
        'HOST': 'ec2-34-204-127-36.compute-1.amazonaws.com',
        'PORT': '5432',
    }
}

CORS_ALLOW_ALL_ORIGINS = True

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

APPEND_SLASH = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/Images/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "Images"),
    os.path.join(BASE_DIR, "Images/profile"),
    os.path.join(BASE_DIR, "static"),
)

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=10),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30)
}
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = 'mytrialacaunt@gmail.com'
EMAIL_HOST_PASSWORD = 'Trial@123'
EMAIL_USE_TLS = True

# EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND")
# EMAIL_HOST = os.environ.get("EMAIL_HOST")
# EMAIL_USE_TLS = True
# EMAIL_PORT = os.getenv("EMAIL_PORT", 587)
# EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
# ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')

LOGIN_URL = '/login'
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warring',
    messages.ERROR: 'alert-danger',
}

BASE_URL = "https://swimtimesolutions.com"


# CELERY_BROKER_URL = 'redis://127.0.0.1:6379'
CELERY_BROKER_URL = 'redis://localhost:6379/0'
# CELERY_RESULT_BACKEND = 'redis://localhost:6379'
# CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Kolkata'

# CELERY_RESULT_BACKEND = 'django-db'
# CELERY_RESULT_BACKEND = 'db+sqlite:///results.db'
# CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# """
# Django settings for SharkDeck project.
#
# Generated by 'django-admin startproject' using Django 3.1.1.
#
# For more information on this file, see
# https://docs.djangoproject.com/en/3.1/topics/settings/
#
# For the full list of settings and their values, see
# https://docs.djangoproject.com/en/3.1/ref/settings/
# """
# import os
# from datetime import timedelta
# from pathlib import Path
#
# from django.contrib import messages
#
# PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
# STATIC_URL = '/static/'
# BASE_DIR = Path(__file__).resolve().parent.parent
# STATICFILES_DIRS = (
#     os.path.join(PROJECT_DIR, 'static'),
# )
# SECRET_KEY = 'jd(2z+97zheo^z41l!u%z4$4of#8+!fept9m79z%0!g$hs-@&0'
#
# # SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True
#
# ALLOWED_HOSTS = ['*']
#
# # Application definition
# AUTH_USER_MODEL = 'user.User'
# INSTALLED_APPS = [
#     'whitenoise.runserver_nostatic',
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',
#     'corsheaders',
#     'rest_framework',
#     'Appointment',
#     'user',
#     'InstructorDashboard',
#     'StripePayment',
#     'ContactUs',
#     'django_seed',
#     'app',
#
# ]
#
# MIDDLEWARE = [
#     'django.middleware.security.SecurityMiddleware',
#     'whitenoise.middleware.WhiteNoiseMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'corsheaders.middleware.CorsMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
# ]
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
#
# ROOT_URLCONF = 'SharkDeck.urls'
#
# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [BASE_DIR / 'templates']
#         ,
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]
#
# WSGI_APPLICATION = 'SharkDeck.wsgi.application'
#
# # Database
# # https://docs.djangoproject.com/en/3.1/ref/settings/#databases
# #
# # if os.environ.get('DATABASE_NAME'):
# #     DATABASES = {
# #         'default': {
# #             'ENGINE': 'django.db.backends.postgresql_psycopg2',
# #             'NAME': os.environ.get('DATABASE_NAME'),
# #             'USER': os.environ.get('DATABASE_USER'),
# #             'PASSWORD': os.environ.get('DATABASE_PASSWORD'),
# #             'HOST': os.environ.get('DATABASE_HOST'),
# #             'PORT': os.environ.get('DATABASE_PORT', default='5432'),
# #         }
# #     }
# # else:
# # #
# DATABASES = {
#     'default': {
#         # 'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         # 'NAME': 'd6ecfhttf73ste',
#         # 'USER': 'nnrdlqzfkglpgg',
#         # 'PASSWORD': 'c2edb63965d64fa5a84b6574d74d0c7ea4c3dcf0f1207d6f358ff96b42dd1428',
#         # 'HOST': 'ec2-34-204-127-36.compute-1.amazonaws.com',
#         # 'PORT': '5432',
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'swim',
#         'USER': 'manoj',
#         'PASSWORD': 'Swim@123',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }
#
# # DATABASES = {
# #     'default': {
# #         'ENGINE': 'django.db.backends.postgresql_psycopg2',
# #         'NAME': 'swimtest',
# #         'USER': 'postgres',
# #         'PASSWORD': '123456',
# #         'HOST': 'localhost',
# #         'PORT': '5432',
# #     }
# # }
#
# CORS_ALLOW_ALL_ORIGINS = True
#
# # Password validation
# # https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators
#
# AUTH_PASSWORD_VALIDATORS = [
#     {
#         'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#     },
# ]
#
# # Internationalization
# # https://docs.djangoproject.com/en/3.1/topics/i18n/
#
# LANGUAGE_CODE = 'en-us'
#
# TIME_ZONE = 'UTC'
#
# USE_I18N = True
#
# USE_L10N = True
#
# USE_TZ = True
#
# APPEND_SLASH = False
#
# # Static files (CSS, JavaScript, Images)
# # https://docs.djangoproject.com/en/3.1/howto/static-files/
#
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# STATIC_URL = '/Images/'
#
# STATICFILES_DIRS = (
#     os.path.join(BASE_DIR, "Images"),
#     os.path.join(BASE_DIR, "Images/profile"),
#     os.path.join(BASE_DIR, "static"),
# )
#
# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': (
#         'rest_framework_simplejwt.authentication.JWTAuthentication',
#     )
# }
# SIMPLE_JWT = {
#     'ACCESS_TOKEN_LIFETIME': timedelta(days=10),
#     'REFRESH_TOKEN_LIFETIME': timedelta(days=30)
# }
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#         },
#     },
#     'root': {
#         'handlers': ['console'],
#         'level': 'INFO',
#     },
# }
#
# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = "smtp.gmail.com"
# EMAIL_PORT = 587
# EMAIL_HOST_USER = 'mytrialacaunt@gmail.com'
# EMAIL_HOST_PASSWORD = 'Trial@123'
# EMAIL_USE_TLS = True
#
# # EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND")
# # EMAIL_HOST = os.environ.get("EMAIL_HOST")
# # EMAIL_USE_TLS = True
# # EMAIL_PORT = os.getenv("EMAIL_PORT", 587)
# # EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
# # EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
# # ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
#
# LOGIN_URL = '/login'
# MESSAGE_TAGS = {
#     messages.DEBUG: 'alert-info',
#     messages.INFO: 'alert-info',
#     messages.SUCCESS: 'alert-success',
#     messages.WARNING: 'alert-warring',
#     messages.ERROR: 'alert-danger',
# }
#
#
# BASE_URL ="http://192.168.1.12:8000"
