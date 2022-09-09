"""
Generated by 'django-admin startproject' using Django 4.0.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

from pathlib import Path

import sentry_sdk
from pypugjs.ext.django.compiler import enable_pug_translations
from sentry_sdk.integrations.django import DjangoIntegration

from my_secrets import secrets

enable_pug_translations()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path.cwd()
SECRET_KEY = secrets.SECRET_KEY
SITE_ID = 1

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
ALLOWED_HOSTS = [
    '*',
    '7379-185-89-39-27.eu.ngrok.io',
]
CORS_ALLOWED_ORIGINS = CSRF_TRUSTED_ORIGINS = CORS_ORIGIN_WHITELIST = [
    'http://localhost:8080',
]
CORS_ALLOW_CREDENTIALS = True  # allow cookies

INSTALLED_APPS = [
    # our own stuff
    "users",
    "meals",
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    # 3rd party apps
    "axes",
    "compressor",
    "corsheaders",
    "django_extensions",
    "django_secrets",
    "post_office",
    "rest_framework",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
]
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "axes.backends.AxesBackend",
]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "loaders": [
                # PyPugJS part:   ##############################
                (
                    "pypugjs.ext.django.Loader",
                    (
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                    ),
                )
            ],
            "builtins": ["pypugjs.ext.django.templatetags"],
        },
    }
]

AUTH_USER_MODEL = "users.User"
ROOT_URLCONF = "settings.urls"
WSGI_APPLICATION = "settings.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
    # PLEASE, as soon as the project gets a lil more serious => use Postgres!
    # https://duckduckgo.com/?q=postgres+vs+mysql&atb=v101-6&iax=videos&ia=videos&iai=emgJtr9tIME
    #############################################################################################
    #  'default': {
    #     'ENGINE': 'django.db.backends.postgresql',
    #     'NAME': 'db_name',
    #     'USER': 'username',
    #     'PASSWORD': secrets.DB_PASSWORD,
    #     'HOST': '127.0.0.1',
    #     'PORT': '5432',
    #     'ATOMIC_REQUESTS': True,  # enables automatic rollback on broken requests
    # }
}
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    "axes_cache": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
AXES_LOGIN_FAILURE_LIMIT = 2
AXES_CACHE = "axes_cache"
AXES_USE_USER_AGENT = True
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/
LANGUAGE_CODE = "de-de"
TIME_ZONE = "CET"
USE_I18N = True
USE_L10N = True
USE_TZ = True


STATICFILES_DIRS = [BASE_DIR / "assets"]
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
]
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
STATIC_ROOT = BASE_DIR / "static"
MEDIA_ROOT = BASE_DIR / "media"
COMPRESS_PRECOMPILERS = (("text/x-sass", "sass {infile} {outfile}"),)
COMPRESS_ENABLED = True


# sentry_sdk.init(
#     dsn=secrets.SENTRY_DSN,  # salat live
#
#     integrations=[DjangoIntegration()],
#
#     # Set traces_sample_rate to 1.0 to capture 100%
#     # of transactions for performance monitoring.
#     # We recommend adjusting this value in production,
#     traces_sample_rate=1.0,
#
#     # If you wish to associate users to errors (assuming you are using
#     # django.contrib.auth) you may enable sending PII data.
#     send_default_pii=True,
#
#     # By default the SDK will try to use the SENTRY_RELEASE
#     # environment variable, or infer a git commit
#     # SHA as release, however you may want to set
#     # something more human-readable.
#     # release="myapp@1.0.0",
# )

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

EMAIL_OVERRIDE_ADDRESS = None
EMAIL_FOOTER = ""
EMAIL_BACKEND = "post_office.EmailBackend"

SILENCED_SYSTEM_CHECKS = ["debug_toolbar.W006"]

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        'meals.utils.CsrfExemptSessionAuthentication'
    ]
}