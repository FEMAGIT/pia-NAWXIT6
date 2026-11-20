"""
Django settings for Ticketing_V2 project
"""
from cryptography.fernet import Fernet
import os
import sys

def find_or_create_chyper_key():
    CHYPER_KEY_FILEPATH = os.path.join(BASE_DIR, 'migatte_no_gokui.txt')
    sys.path.insert(1, BASE_DIR)

    if os.path.isfile(CHYPER_KEY_FILEPATH):
        with open(CHYPER_KEY_FILEPATH, 'rb') as f:
            chyper_key = f.readline()
        f.close()
        return chyper_key
    else:
        chyper_key = Fernet.generate_key()
        with open(CHYPER_KEY_FILEPATH, 'wb') as f:
            f.write(chyper_key)
        f.close()
        return chyper_key

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
CHYPER_KEY = find_or_create_chyper_key()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('1', 'true', 'yes')

ALLOWED_HOSTS = [h.strip() for h in os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]


# Application definition

INSTALLED_APPS = [
    'django_tables2',
    'material',
    'bootstrap4',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
 #   'ticketing',
    'corsheaders',
    #'debug_toolbar',
    #'pympler',
    'django_extensions',
    'rest_framework',
    'accounts',
    'rest_framework.authtoken',
    'channels',
#    'socoin',
    # 'qr_code',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.BrokenLinkEmailsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    #'django_cprofile_middleware.middleware.ProfilerMiddleware'
]

ROOT_URLCONF = 'Ticketing_V2.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
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

WSGI_APPLICATION = 'Ticketing_V2.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#datab 'postgres',

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DB_NAME', 'videocall'),
        'USER': os.environ.get('DB_USER', 'videocall'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    },
}

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

FILE_UPLOAD_HANDLERS = [
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler"
]

LANGUAGE_CODE = 'it'

TIME_ZONE = 'Europe/Rome'

USE_I18N = True

USE_L10N = True

USE_TZ = False

STATIC_URL = '/video/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'video/static')

MEDIA_URL = '/media/upload/'

PROCESS_EXPORT_URL = '/process_export/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media/upload/')

PROCESS_EXPORT_ROOT = os.path.join(BASE_DIR, 'process_export/')

SESSION_COOKIE_AGE = 20*60

CSRF_COOKIE_SECURE = False

#INTERNAL_IPS = ['127.0.0.1']




ASGI_APPLICATION = "Ticketing_V2.routing.application"

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}






# Default settings
BOOTSTRAP4 = {

    # The complete URL to the Bootstrap CSS file
    # Note that a URL can be either a string,
    # e.g. "https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css",
    # or a dict like the default value below.
    "css_url": {
        "href": "https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css",
        "integrity": "sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T",
        "crossorigin": "anonymous",
    },

    # The complete URL to the Bootstrap JavaScript file
    "javascript_url": {
        "url": "https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js",
        "integrity": "sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM",
        "crossorigin": "anonymous",
    },

    # The complete URL to the Bootstrap CSS file (None means no theme)
    "theme_url": None,

    # The URL to the jQuery JavaScript file (full)
    "jquery_url": {
        "url": "https://code.jquery.com/jquery-3.3.1.min.js",
        "integrity": "sha384-tsQFqpEReu7ZLhBV2VZlAu7zcOV+rXbYlF2cqB8txI/8aZajjp4Bqd+V6D5IgvKT",
        "crossorigin": "anonymous",
    },

    # The URL to the jQuery JavaScript file (slim)
    "jquery_slim_url": {
        "url": "https://code.jquery.com/jquery-3.2.1.slim.min.js",
        "integrity": "sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN",
        "crossorigin": "anonymous",
    },

    # The URL to the Popper.js JavaScript file (slim)
    "popper_url": {
        "url": "https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.12.9/umd/popper.min.js",
        "integrity": "sha384-ApNbgh9B+Y1QKtv3Rn7W3mgPxhU9K/ScQsAP7hUibX39j7fakFPskvXusvfa0b4Q",
        "crossorigin": "anonymous",
    },

    # Put JavaScript in the HEAD section of the HTML document (only relevant if you use bootstrap4.html)
    'javascript_in_head': False,

    # Include jQuery with Bootstrap JavaScript False|falsy|slim|full (default=False)
    # False - means tag bootstrap_javascript use default value - `falsy` and does not include jQuery)
    'include_jquery': 'slim',

    # Label class to use in horizontal forms
    'horizontal_label_class': 'col-md-3',

    # Field class to use in horizontal forms
    'horizontal_field_class': 'col-md-9',

    # Set placeholder attributes to label if no placeholder is provided
    'set_placeholder': True,

    # Class to indicate required (better to set this in your Django form)
    'required_css_class': '',

    # Class to indicate error (better to set this in your Django form)
    'error_css_class': 'has-error',

    # Class to indicate success, meaning the field has valid input (better to set this in your Django form)
    'success_css_class': 'has-success',

    # Renderers (only set these if you have studied the source and understand the inner workings)
    'formset_renderers':{
        'default': 'bootstrap4.renderers.FormsetRenderer',
    },
    'form_renderers': {
        'default': 'bootstrap4.renderers.FormRenderer',
    },
    'field_renderers': {
        'default': 'bootstrap4.renderers.FieldRenderer',
        'inline': 'bootstrap4.renderers.InlineFieldRenderer',
    },
}

DATABASE_ROUTERS = ['accounts.dbRouter.App1DBRouter',]


# Indirizzi pubblici del servizio (configurabili da variabile d'ambiente).
BASE_URL = os.environ.get('VIDEOCALL_BASE_URL', 'https://videocall.example.com/')
WS_BASE_URL = os.environ.get('VIDEOCALL_WS_BASE_URL', 'wss://videocall.example.com')

# Token che autorizza la registrazione automatica di nuovi occhiali in
# /video/api/smartglass_login/. Vuoto = registrazione disattivata.
SMARTGLASS_REGISTRATION_TOKEN = os.environ.get('SMARTGLASS_REGISTRATION_TOKEN', '')

WS_SYSTEM_URL = '/ws/system/'

AUTH_USER_MODEL = 'accounts.User'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'INFO',  # Setta il livello di log a DEBUG
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'django_debug.log'),  # File di log Django
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],  # Log sia su console che su file
            'level': 'INFO',
            'propagate': True,
        },
    },
}
