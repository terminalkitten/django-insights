from django.apps import AppConfig


class TestAppConfig(AppConfig):
    name = 'project.testapp'
    verbose_name = 'Django Insights TestApp'
    default_auto_field = 'django.db.models.BigAutoField'
