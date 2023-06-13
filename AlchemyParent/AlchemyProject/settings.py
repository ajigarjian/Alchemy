"""
Django settings for AlchemyProject project.

Generated by 'django-admin startproject' using Django 4.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
import secrets
import dj_database_url
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# Django requires a unique secret key for each Django app, that is used by several of its
# security features. To simplify initial setup (without hardcoding the secret in the source
# code) we set this to a random value every time the app starts. However, this will mean many
# Django features break whenever an app restarts (for example, sessions will be logged out).
# In your production Heroku apps you should set the `DJANGO_SECRET_KEY` config var explicitly.
# Make sure to use a long unique value, like you would for a password. See:
# https://docs.djangoproject.com/en/4.2/ref/settings/#std-setting-SECRET_KEY
# https://devcenter.heroku.com/articles/config-vars
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    default=secrets.token_urlsafe(nbytes=64),
)

# The `DYNO` env var is set on Heroku CI, but it's not a real Heroku app, so we have to
# also explicitly exclude CI:
# https://devcenter.heroku.com/articles/heroku-ci#immutable-environment-variables
IS_HEROKU_APP = os.environ.get('DYNO') is not None and os.environ.get('CI') is None

# SECURITY WARNING: don't run with debug turned on in production!
if not IS_HEROKU_APP:
    DEBUG = True

# On Heroku, it's safe to use a wildcard for `ALLOWED_HOSTS``, since the Heroku router performs
# validation of the Host header in the incoming HTTP request. On other platforms you may need
# to list the expected hostnames explicitly to prevent HTTP Host header attacks. See:
# https://docs.djangoproject.com/en/4.2/ref/settings/#std-setting-ALLOWED_HOSTS
if IS_HEROKU_APP:
    ALLOWED_HOSTS = ["*"]
else:
    ALLOWED_HOSTS = []

#Added to provide functionality for Django-tailwind
TAILWIND_APP_NAME = 'theme'

#Added to provide functionality for Django-tailwind
INTERNAL_IPS = [
    "127.0.0.1",
]

# Application definition

INSTALLED_APPS = [
    'AlchemyApp', #Added after creating App within Project
    'tailwind', #Added to provide functionality for Django-tailwind
    'theme', #Added to provide functionality for Django-tailwind
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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

ROOT_URLCONF = 'AlchemyProject.urls'

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

        'libraries':{ #Added to detect custom templatetags folder with __init__.py added and _template_filters.py to create custom get_item tag function
            'template_filters': 'AlchemyApp.templatetags.template_filters',
            
            }

        },
    },
]

WSGI_APPLICATION = 'AlchemyProject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# if IS_HEROKU_APP:
#     # In production on Heroku the database configuration is derived from the `DATABASE_URL`
#     # environment variable by the dj-database-url package. `DATABASE_URL` will be set
#     # automatically by Heroku when a database addon is attached to your Heroku app. See:
#     # https://devcenter.heroku.com/articles/provisioning-heroku-postgres
#     # https://github.com/jazzband/dj-database-url
#     DATABASES = {
#         "default": dj_database_url.config(
#             conn_max_age=600,
#             conn_health_checks=True,
#             ssl_require=True,
#         ),
#     }
# else:
    # When running locally in development or in CI, a sqlite database file will be used instead
    # to simplify initial setup. Longer term it's recommended to use Postgres locally too.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Added this in to create run custom authentication backend before default one for users trying to log in
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Django's default authentication backend
    'AlchemyApp.backends.CustomUserAuthenticationBackend',  # Our custom authentication backend
]


AUTH_USER_MODEL = 'AlchemyApp.CustomUser'

# Changing the default login url from /accounts/login to /login for @login_required.
LOGIN_URL = '/login'

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
     BASE_DIR / 'AlchemyApp' / 'static',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'