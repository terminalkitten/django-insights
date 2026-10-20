from importlib import import_module

from django.apps import AppConfig


class InsightAppConfig(AppConfig):
    name = 'django_insights'
    label = 'insights'
    verbose_name = 'Django Insights'

    default_auto_field = 'django.db.models.AutoField'

    def ready(self) -> None:
        import_module('django_insights.checks')
