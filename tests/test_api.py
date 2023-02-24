from django.test import TestCase

from django_insights.registry import registry


class ApiTests(TestCase):
    def test_autodiscover_registry(self):
        registry.autodiscover_insights()
        assert registry.registered_insights
