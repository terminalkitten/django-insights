import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from django_insights.database import check_settings
from django_insights.registry import registry
from project.settings import DATABASES
from project.testapp.models import TestAppUser

COPY_DATABASES = DATABASES.copy()
COPY_DATABASES.pop('insights')


class ApiTests(TestCase):
    @override_settings(DATABASES=COPY_DATABASES)
    def test_throw_error_no_insights_db_configured(self):
        with pytest.raises(ImproperlyConfigured):
            check_settings()

    def test_autodiscover_registry(self):
        registry.autodiscover_insights()
        assert registry.registered_insights

    def test_no_testapp_users(self):
        assert TestAppUser.objects.count() == 0
