import pytest
from django.core import management
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from django_insights.database import check_settings
from django_insights.models import Counter
from django_insights.registry import registry
from project.settings.test import DATABASES
from project.testapp.models import AppUser
from tests.utils import collect_insights

COPY_DATABASES = DATABASES.copy()
COPY_DATABASES.pop('insights')


class ApiTests(TestCase):
    databases = ['default', 'insights']

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        management.call_command('seed_db')
        collect_insights()

    @override_settings(DATABASES=COPY_DATABASES)
    def test_throw_error_no_insights_db_configured(self):
        with pytest.raises(ImproperlyConfigured):
            check_settings()

    def test_autodiscover_registry(self):
        assert registry.registered_insights

    def test_no_app_users_found(self):
        assert AppUser.objects.count() == 0

    def test_has_counter_metric(self):
        counter = Counter.objects.first()
        assert counter.value == 0
