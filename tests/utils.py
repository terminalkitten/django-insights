import pytest

from django_insights.registry import registry


@pytest.mark.django_db(True)
def collect_insights() -> None:
    from django_insights.metrics import metrics

    registry.autodiscover_insights()
    metrics.collect()
