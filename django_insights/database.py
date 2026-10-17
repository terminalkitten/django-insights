from typing import Any

from django.db.models import Model

app_labels = {"insights"}
database_entry = "insights"


class Router:
    def db_for_read(self, model: type[Model], **hints: Any) -> str | None:
        if model._meta.app_label in app_labels:
            return "insights"
        return None

    def db_for_write(self, model: type[Model], **hints: Any) -> str | None:
        if model._meta.app_label in app_labels:
            return "insights"

    def allow_relation(self, obj1: Model, obj2: Model, **hints: Any) -> bool | None:
        if obj1._meta.app_label in app_labels or obj2._meta.app_label in app_labels:
            return True
        return None

    def allow_migrate(self, db: str, app_label: str, **hints: Any) -> bool | None:
        if app_label in app_labels:
            return db == database_entry
        return None
