"""
Generated by 'django-admin startproject' using Django 4.0.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

from pathlib import Path

from pypugjs.ext.django.compiler import enable_pug_translations

from my_secrets import secrets
from icecream import install

install()

enable_pug_translations()


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path.cwd()
SECRET_KEY = secrets.SECRET_KEY
SITE_ID = 1

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
ALLOWED_HOSTS = [
    "*",
    "https://menue.luises-familienbande.de",
    "https://emmas-imbiss.de",
]
CORS_ALLOWED_ORIGINS = CSRF_TRUSTED_ORIGINS = CORS_ORIGIN_WHITELIST = [
    "http://localhost:8080",
    "https://menue.luises-familienbande.de",
    "https://emmas-imbiss.de",
]
CORS_ALLOW_CREDENTIALS = True  # allow cookies

INSTALLED_APPS = [
    # our own stuff
    "users",
    "invoices",
    "meals",
    "jazzmin",
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    # 3rd party apps
    # "axes",
    "compressor",
    "corsheaders",
    "django_extensions",
    "django_filters",
    "django_secrets",
    # "post_office",
    "rest_framework",
    "sass_processor",
    "ckeditor",
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
    # "axes.middleware.AxesMiddleware",
]
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    # "axes.backends.AxesBackend",
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
    "sass_processor.finders.CssFinder",
]
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
STATIC_ROOT = str(BASE_DIR / "static")
MEDIA_ROOT = str(BASE_DIR / "media")
SASS_TEMPLATE_EXTS = [".html", ".pug"]


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

SILENCED_SYSTEM_CHECKS = ["debug_toolbar.W006", 'ckeditor.W001']

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    "DEFAULT_AUTHENTICATION_CLASSES": ["meals.utils.CsrfExemptSessionAuthentication"],
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        # Optional: Hinzufügen von Browsable API, wenn gewünscht
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

JAZZMIN_SETTINGS = {
    # title of the window (Will default to current_admin_site.site_title if absent or None)
    "site_title": "Menü-Admin",
    # Title on the login screen (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_header": "Admin",
    # Title on the brand (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_brand": "Admin",
    # Logo to use for your site, must be present in static files, used for brand on top left
    # "site_logo": "books/img/logo.png",
    # Logo to use for your site, must be present in static files, used for login form logo (defaults to site_logo)
    "login_logo": None,
    # Logo to use for login form in dark themes (defaults to login_logo)
    "login_logo_dark": None,
    # CSS classes that are applied to the logo above
    "site_logo_classes": "img-circle",
    # Relative path to a favicon for your site, will default to site_logo if absent (ideally 32x32 px)
    "site_icon": None,
    # Welcome text on the login screen
    "welcome_sign": "Willkommen im Admin",
    # Copyright on the footer
    "copyright": "Andy Grabow",
    # The model admin to search from the search bar, search bar omitted if excluded
    "search_model": "meals.Meal",
    # Field name on user model that contains avatar ImageField/URLField/Charfield or a callable that receives the user
    "user_avatar": None,
    ############
    # Top Menu #
    ############
    # Links to put along the top menu
    "topmenu_links": [
        {"name": "Speisekarte", "url": "/kueche/"},
        # App with dropdown menu to all its models pages (Permissions checked against models)
        {"model": "meals.meal"},
    ],
    #############
    # User Menu #
    #############
    # Additional links to include in the user menu on the top right ("app" url type is not allowed)
    "usermenu_links": [
        # {"model": "auth.user"}
    ],
    #############
    # Side Menu #
    #############
    # Whether to display the side menu
    "show_sidebar": True,
    # Whether to aut expand the menu
    "navigation_expanded": True,
    # Hide these apps when generating side menu e.g (auth)
    "hide_apps": ["sites", "auth"],
    # Hide these models when generating side menu (e.g auth.user)
    "hide_models": [],
    # List of apps (and/or models) to base side menu ordering off of (does not need to contain all apps/models)
    "order_with_respect_to": [],
    # Custom links to append to app groups, keyed on app name
    # "custom_links": {
    #     "books": [{
    #         "name": "Make Messages",
    #         "url": "make_messages",
    #         "icon": "fas fa-comments",
    #         "permissions": ["books.view_book"]
    #     }]
    # },
    # Custom icons for side menu apps/models See https://fontawesome.com/icons?d=gallery&m=free&v=5.0.0,5.0.1,5.0.10,5.0.11,5.0.12,5.0.13,5.0.2,5.0.3,5.0.4,5.0.5,5.0.6,5.0.7,5.0.8,5.0.9,5.1.0,5.1.1,5.2.0,5.3.0,5.3.1,5.4.0,5.4.1,5.4.2,5.13.0,5.12.0,5.11.2,5.11.1,5.10.0,5.9.0,5.8.2,5.8.1,5.7.2,5.7.1,5.7.0,5.6.3,5.5.0,5.4.2
    # for the full list of 5.13.0 free icon classes
    "icons": {
        "meals.day": "fas fa-calendar-day",
        "meals.week": "fas fa-calendar-week",
        "meals.meal": "fas fa-drumstick-bite",
        "users.user": "fas fa-users",
        "meals.location": "fas fa-map-marker-alt",
        "meals.suggestion": "fas fa-lightbulb",
    },
    # Icons that are used when one is not manually specified
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    #################
    # Related Modal #
    #################
    # Use modals instead of popups
    "related_modal_active": False,
    #############
    # UI Tweaks #
    #############
    # Relative paths to custom CSS/JS scripts (must be present in static files)
    "custom_css": None,
    "custom_js": None,
    # Whether to show the UI customizer on the sidebar
    "show_ui_builder": False,
    ###############
    # Change view #
    ###############
    # Render out the change view as a single form, or in tabs, current options are
    # - single
    # - horizontal_tabs (default)
    # - vertical_tabs
    # - collapsible
    # - carousel
    "changeform_format": "horizontal_tabs",
    # override change forms on a per modeladmin basis
    "changeform_format_overrides": {"auth.user": "collapsible", "auth.group": "vertical_tabs"},
    # Add a language dropdown into the admin
    "language_chooser": False,
}

CKEDITOR_CONFIGS = {
    "default": {
        "toolbar": "Custom",
        "toolbar_Custom": [
            ["Bold", "Italic", "Underline"],
        ],
    }
}
