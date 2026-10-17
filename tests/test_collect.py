import pytest
from django.core import management

from django_insights.models import App, Bucket, Counter, Gauge
from django_insights.registry import registry
from tests.utils import SEED_AUTHORS, SEED_BOOKS

pytestmark = pytest.mark.django_db(databases=['default', 'insights'])


def test_autodiscover_registers_insights(collected):
    assert registry.registered_insights


def test_counters_match_seeded_data(collected):
    assert Counter.objects.get(label='count_authors').value == SEED_AUTHORS
    assert Counter.objects.get(label='count_books').value == SEED_BOOKS


def test_apps_use_module_label(collected):
    assert App.objects.filter(label='Books').exists()


def test_gauge_is_collected(collected):
    assert Gauge.objects.filter(label='avg_books_per_author').exists()


def test_every_bucket_type_is_collected(collected):
    kinds = {
        'timeseries': Bucket.objects.timeseries(),
        'scatterplot': Bucket.objects.scatterplots(),
        'barchart': Bucket.objects.barcharts(),
        'hbarchart': Bucket.objects.hbarcharts(),
    }
    for name, queryset in kinds.items():
        assert queryset.exists(), name


def test_collect_twice_does_not_duplicate(collected):
    from django_insights.metrics import metrics

    before = Counter.objects.count(), Bucket.objects.count()
    metrics.collect(reset=True)
    assert (Counter.objects.count(), Bucket.objects.count()) == before


def test_collect_command_runs(collected):
    Counter.objects.all().delete()
    management.call_command('collect_insights')
    assert Counter.objects.filter(label='count_authors').exists()
