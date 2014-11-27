"""
Django settings for dbs project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement

# localsettings is used to store site depandant settings
from .site_settings import (
    SECRET_KEY, ALLOWED_HOSTS, DATABASES,
    DEBUG, DBDEBUG, TEMPLATE_DEBUG,
    ADMINS, MANAGERS, SERVER_EMAIL,
    LANGUAGE_CODE, TIME_ZONE, LANGUAGES,
    MEDIA_ROOT, MEDIA_URL, STATIC_ROOT, STATIC_URL,
    BROKER_URL, CELERY_RESULT_BACKEND, CELERY_TIMEZONE,
)


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dbs',
    'dbs.api',
    'dbs.web',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'dbs.urls'

WSGI_APPLICATION = 'dbs.wsgi.application'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'loggers': {
        '': {
            'handlers': DEBUG and ['console'] or ['console', 'mail_admins'],
            'level':    DEBUG and 'DEBUG'     or 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.db.backends': {
            'level': DBDEBUG and 'DEBUG' or 'INFO',
            'propagate': True,
        },
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Celery configuration
BROKER_TRANSPORT_OPTIONS = {
    'fanout_prefix': True,
    'fanout_patterns': True,
    'visibility_timeout': 3600,  # 1 hour
}
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'
CELERY_ACCEPT_CONTENT = ['json', 'pickle']
CELERY_ENABLE_UTC = True
