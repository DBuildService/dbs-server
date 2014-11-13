# -*- coding: utf-8 -*-
# vim: ft=python

from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = '/var/lib/dbs'

# SECURITY WARNING: keep the secret key used in production secret!
with open(os.path.join(BASE_DIR, 'secret_key'), 'rb') as f:
    SECRET_KEY = repr(f.read())

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG   = os.environ.get('DBS_DEBUG', False) and True or False
DBDEBUG = os.environ.get('DBS_DEBUG', False) == 'DB'

TEMPLATE_DEBUG = 'TEMPLATE_DEBUG' in os.environ and os.environ['TEMPLATE_DEBUG'] and True or False

ALLOWED_HOSTS = ['*']

# Emails
# https://docs.djangoproject.com/en/1.7/ref/settings/#std:setting-ADMINS
# https://docs.djangoproject.com/en/1.7/ref/settings/#std:setting-MANAGERS
# https://docs.djangoproject.com/en/1.7/ref/settings/#std:setting-SERVER_EMAIL
ADMINS = (
    ('Jakub Dorňák',   'jdornak+dbs@redhat.com'),
)
MANAGERS = ADMINS
SERVER_EMAIL = 'admin@dbs.org'

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'data', 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en'

TIME_ZONE = 'UTC'

LANGUAGES = (
    ('en', 'English'),
)

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, 'htdocs', 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'htdocs', 'static')

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/
STATIC_URL = '/static/'

# Absolute path to the directory repos should be synced to.
REPOS_ROOT = os.path.join(BASE_DIR, 'htdocs', 'repos')

# URL prefix for repo.
REPOS_URL  = '/repos/'

# Absolute path to the directory used by yum cache
YUM_CACHE_ROOT = '/tmp/dbs-yum-cache'

# Absolute path to the directory to be used as rpm _topdir
RPMBUILD_TOPDIR = '/tmp/dbs-rpmbuild'

# Celery configuration
BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TIMEZONE = 'Europe/Prague'

