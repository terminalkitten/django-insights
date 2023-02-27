from project.settings.base import *  # noqa

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
    "insights": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
}
