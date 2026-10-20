from typing import Any

from django.core.management.base import BaseCommand, CommandError

from django_insights.metrics import metrics
from django_insights.registry import registry


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(self.style.HTTP_INFO('[Django Insights] - Collect insights'))

        registry.autodiscover_insights()
        total = len(registry.registered_insights)
        failures = metrics.collect(reset=True)

        for failure in failures:
            self.stderr.write(
                self.style.ERROR(f'{failure.module}.{failure.label}: {failure.error!r}')
            )
        if failures:
            raise CommandError(f'{len(failures)} of {total} insights failed')
