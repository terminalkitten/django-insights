from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

app_labels = {"insights"}
database_entry = "insights"


def check_settings():
    if database_entry not in settings.DATABASES:
        raise ImproperlyConfigured()


class Router:
    def db_for_read(self, model, **hints):
        if model._meta.app_label in app_labels:
            return "insights"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in app_labels:
            return "insights"

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label in app_labels or obj2._meta.app_label in app_labels:
            return True
        return None

    def allow_migrate(self, db, app_label, **hints):
        if app_label in app_labels:
            return db == database_entry
        return None
