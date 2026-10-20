from django.apps import AppConfig


class TestAppTasksConfig(AppConfig):
    name = 'project.testapp.tasks'
    label = 'tasks'
    default_auto_field = 'django.db.models.BigAutoField'
