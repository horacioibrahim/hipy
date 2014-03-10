"""
Django settings for blongo project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

from settings import * 

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

DBNAME = 'papyDB'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '!%rfhp&v(dxt)@y%6vu$^82c+uc(sad*_7w=&pty(i*f!@14ne'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

