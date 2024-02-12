from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-yasg^0$m=5x)iihj!9@hq02+7ds9##=!-3-(2#7(16azwjskf1')

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', '').strip("[]").split(',')
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS]

# Application definition
INSTALLED_APPS = [
    'api',
    'rest_framework',
]

MIDDLEWARE = [
]

ROOT_URLCONF = 'api.urls'

WSGI_APPLICATION = 'api.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': config('DATABASE_ENGINE', default='django.db.backends.mysql'),
        'NAME': config('DATABASE_NAME', default='data_scraper'),
        'USER': config('DATABASE_USER', default='zanelesp'),
        'PASSWORD': config('DATABASE_PASSWORD', default='xtBNfC@-Vb3E@n*erDc8Y'),
        'HOST': config('DATABASE_HOST', default='127.0.0.1'),
        'PORT': config('DATABASE_PORT', default=3306, cast=int),
    }
}


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'UNAUTHENTICATED_USER': None,
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
}
