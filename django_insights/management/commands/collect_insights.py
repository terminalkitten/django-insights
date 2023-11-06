from django.core.management.base import BaseCommand

from django_insights.metrics import metrics
from django_insights.registry import registry


class Command(BaseCommand):

    """Show all registered audit events"""

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('[Django Insights] - Collect insights'))

        # Auto-discover
        registry.autodiscover_insights()

        # Save metrics
        metrics.collect(reset=True)
