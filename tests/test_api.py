import pytest
from django.core import management
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.urls import reverse

from django_insights.database import check_settings
from django_insights.models import App, Bucket, Counter
from django_insights.registry import registry
from project.settings.test import DATABASES
from project.testapp.users.models import AppUser
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

    def test_one_app_user_found(self):
        assert AppUser.objects.count() == 1

    def test_count_authors(self):
        counter = Counter.objects.get(label="count_authors")
        assert counter.value == 2000

    def test_count_books(self):
        counter = Counter.objects.get(label="count_books")
        assert counter.value == 5000


class ViewTests(TestCase):
    databases = ['default', 'insights']

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        management.call_command('seed_db')
        collect_insights()

    def setUp(self):
        self.user = AppUser.objects.create(email='viewer@example.com')

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('insights:insight_dashboard'))
        assert response.status_code == 302

    def test_chart_requires_login(self):
        bucket = Bucket.objects.first()
        response = self.client.get(reverse('insights:insight_chart', args=[bucket.pk]))
        assert response.status_code == 302

    def test_dashboard_renders(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('insights:insight_dashboard'))
        assert response.status_code == 200

    def test_app_view_renders(self):
        self.client.force_login(self.user)
        for app in App.objects.all():
            response = self.client.get(reverse('insights:insight_app', args=[app.pk]))
            assert response.status_code == 200

    def test_every_bucket_renders_png(self):
        self.client.force_login(self.user)
        assert Bucket.objects.exists()
        for bucket in Bucket.objects.all():
            response = self.client.get(
                reverse('insights:insight_chart', args=[bucket.pk])
            )
            assert response.status_code == 200
            assert response.content.startswith(b'\x89PNG')

    def test_unknown_bucket_is_404(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('insights:insight_chart', args=[0]))
        assert response.status_code == 404

    def test_chart_ignores_malicious_theme_cookie(self):
        self.client.force_login(self.user)
        self.client.cookies['theme'] = '../../evil'
        bucket = Bucket.objects.first()
        response = self.client.get(reverse('insights:insight_chart', args=[bucket.pk]))
        assert response.status_code == 200

    def test_pdf_view_renders(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('insights:insight_pdf'))
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'
        assert response.content.startswith(b'%PDF')

        import pymupdf

        document = pymupdf.open('pdf', response.content)
        assert 3 <= len(document) < 100  # cover, counters, charts; no pagination loop
        assert 'Insights' in document[0].get_text()
        assert any(page.get_images() for page in document)

    def test_collect_twice_does_not_duplicate(self):
        from django_insights.metrics import metrics

        before = Counter.objects.count()
        metrics.collect(reset=True)
        assert Counter.objects.count() == before

    def test_charts_do_not_use_pyplot(self):
        import sys

        self.test_every_bucket_renders_png()
        assert 'matplotlib.pyplot' not in sys.modules
