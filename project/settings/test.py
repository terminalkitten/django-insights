from project.settings.base import *

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
    "insights": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
}

INSIGHTS_THEME = None
