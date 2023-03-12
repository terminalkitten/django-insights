from __future__ import annotations

import os

import django

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SECRET_KEY = "NOTASECRET"


DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "db/testapp.db"},
    "insights": {"ENGINE": "django.db.backends.sqlite3", "NAME": "db/insights.db"},
}

DATABASE_ROUTERS = ['django_insights.database.Router']

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}

ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "project.testapp",
    "django_insights",
]

MIDDLEWARE_CLASSES = (
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)


AUTH_USER_MODEL = "testapp.AppUser"

ROOT_URLCONF = "project.urls"
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True

if django.VERSION < (4, 0):
    USE_L10N = True

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

USE_TZ = True


# Django Insights settings

# Custom app name
INSIGHTS_APP_NAME = "Bezamon"

# Menu translation
INSIGHTS_MENU = {'project.testapp.insights': 'Books'}

# Quality of chart images
INSIGHTS_CHART_DPI = 400

# Change primary color
INSIGHTS_CHART_PRIMARY_COLOR = "#fde047"
