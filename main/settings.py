"""
Django settings for blongo project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
DEBUG_PROPAGATE_EXCEPTIONS = True

TEMPLATE_DEBUG = False

ALLOWED_HOSTS = [
    '.hipy.co', 
]

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'main', 'templates'),
)

# Application definition
TEST_RUNNER = 'main.custom_runner.MongoTestRunner'

MONGO_DATABASES = {
    'your_DB' : 'your_alias'
}
MONGO_PORT = 27017
MONGO_HOST = 'localhost'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'mongoengine.django.mongo_auth',
    'blog',
    'feedback360',
    'disqus',
)

AUTH_USER_MODEL = 'mongo_auth.MongoUser'
MONGOENGINE_USER_DOCUMENT = 'blog.models.User' #'mongoengine.django.auth.User'

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.messages.context_processors.messages',
)

SESSION_ENGINE = 'mongoengine.django.sessions'

# SESSION_SERIALIZER (1.5.3+) is required in Django 1.6 as the default serializer is based around JSON and
# doesn't know how to convert bson.objectid.ObjectId. And latest Django 1.6+?
SESSION_SERIALIZER = 'mongoengine.django.sessions.BSONSerializer'

AUTHENTICATION_BACKENDS = (
    'mongoengine.django.auth.MongoEngineBackend',
)

ROOT_URLCONF = 'main.urls'

WSGI_APPLICATION = 'main.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.dummy',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False

LOGIN_URL = '/login/'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

#STATIC_ROOT = os.path.join(BASE_DIR,  "public")

STATICFILES_DIRS = (
     os.path.join(BASE_DIR, 'assets'),
)

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATIC_URL = '/static/'
MEDIA_URL = '/media/'

##########################################
# FIXME: Email settings for Amazon AWS SES
##########################################
AWS_SES_RETURN_PATH = 'your_mail@example.com'
DEFAULT_FROM_EMAIL = 'Your Name <your_name@example.com>'
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_ACCESS_KEY_ID = 'AWS_ACCESS_KEY_ID'
AWS_SECRET_ACCESS_KEY = 'AWS_SECRET_ACCESS_KEY'
DKIM_DOMAIN = 'example.com'
DKIM_SELECTOR = 'ses'
DKIM_PRIVATE_KEY = '''
-----BEGIN RSA PRIVATE KEY-----
EXAMPLEMIICXQIBAAKBgQCsVGwlaCGBbGbTwx59cCIxsaSPrgeu9AZoC9AZoCvDC
w143A/SeNmjMcf3TfaTSdNZLUX0O84dOnZdijVDc5qc7Fx1hM27iIfWM9hwFKZC6
hJgKJIMzRQJBAM97UzjUED6a42hWUSq/GhKN2X3IzZ7FWBQbygAvnopg4wEr3DzE
gVOMG1gzAh+m28uDm/OG8Yz3CRuL57ONLYONEEXAMPLE
-----END RSA PRIVATE KEY-----
'''

# Celery with MongoDB as broker
CELERY_RESULT_BACKEND = 'mongodb'
CELERY_MONGODB_BACKEND_SETTINGS = {
    'host': '127.0.0.1',
    'port': 27017,
    'database': 'celery',
    'taskmeta_collection': 'taskmeta',
}

# DISQUS SETTINGS
DISQUS_API_KEY = 'DISQUS_API_KEY'
DISQUS_WEBSITE_SHORTNAME = 'Example'
DISQUS_URL = 'http://example.com'

