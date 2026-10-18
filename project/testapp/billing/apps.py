from django.apps import AppConfig


class TestAppBillingConfig(AppConfig):
    name = 'project.testapp.billing'
    label = 'billing'
    default_auto_field = 'django.db.models.BigAutoField'
