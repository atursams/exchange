"""Django settings for mainsite project."""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '_j6_=7+s^ou52ib#+t=w%81m(%!rk1(7o1=d6@94s9#!zn3x1z'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
]

MIDDLEWARE = [
]

ROOT_URLCONF = 'mainsite.urls'

TEMPLATES = [
]

WSGI_APPLICATION = 'mainsite.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
CACHE_LIFE_TIME = 10

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'