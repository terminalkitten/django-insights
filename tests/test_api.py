import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from django_insights.database import check_settings
from django_insights.registry import registry
from project.settings import DATABASES

CLONED_DATABASES = DATABASES.copy()
CLONED_DATABASES.pop('insights')


class ApiTests(TestCase):
    @override_settings(DATABASES=CLONED_DATABASES)
    def test_throw_error_no_insights_db_configured(self):
        with pytest.raises(ImproperlyConfigured):
            check_settings()

    def test_autodiscover_registry(self):
        registry.autodiscover_insights()
        assert registry.registered_insights
