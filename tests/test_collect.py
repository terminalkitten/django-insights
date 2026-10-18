import pytest
from django.core import management
from django.core.management.base import CommandError
from django.db import IntegrityError

from django_insights.exceptions import InsightsError
from django_insights.metrics import metrics
from django_insights.models import App, Bucket, Counter, Gauge
from django_insights.registry import registry
from tests.utils import SEED_MESSAGES, SEED_USERS

pytestmark = pytest.mark.django_db(databases=['default', 'insights'])


def test_autodiscover_registers_insights(collected):
    assert registry.registered_insights


def test_counters_match_seeded_data(collected):
    assert Counter.objects.get(label='count_users').value == SEED_USERS
    assert Counter.objects.get(label='count_messages').value == SEED_MESSAGES


def test_apps_use_module_label(collected):
    assert set(App.objects.values_list('label', flat=True)) == {
        'Workspace',
        'Users',
        'Billing',
        'Tasks',
    }


def test_gauge_is_collected(collected):
    assert Gauge.objects.filter(label='avg_members_per_workspace').exists()


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
    before = Counter.objects.count(), Bucket.objects.count()
    metrics.collect(reset=True)
    assert (Counter.objects.count(), Bucket.objects.count()) == before


def test_collect_command_runs(collected):
    Counter.objects.all().delete()
    management.call_command('collect_insights')
    assert Counter.objects.filter(label='count_users').exists()


def write_then_fail():
    App.objects.create(module='tests.ghost')
    raise ValueError('boom')


@pytest.fixture
def broken_insight(collected, monkeypatch):
    insights = [
        *registry.registered_insights,
        ('tests', 'broken', 'q', write_then_fail),
    ]
    monkeypatch.setattr(registry, 'registered_insights', insights)


def test_collect_reports_no_failures_when_everything_works(collected):
    assert metrics.collect(reset=True) == []


def test_a_failing_insight_does_not_stop_the_others(broken_insight, caplog):
    failures = metrics.collect(reset=True)

    assert [(f.module, f.label) for f in failures] == [('tests', 'broken')]
    assert Counter.objects.filter(label='count_users').exists()
    assert 'Insight tests.broken failed' in caplog.text


def test_a_failing_insight_leaves_no_partial_writes(broken_insight):
    metrics.collect(reset=True)
    assert not App.objects.filter(module='tests.ghost').exists()


def test_a_failed_collect_keeps_the_previous_metrics(collected, monkeypatch):
    before = Counter.objects.count()

    def duplicate(*args, **kwargs):
        raise IntegrityError('UNIQUE constraint failed')

    monkeypatch.setattr(Counter.objects, 'bulk_create', duplicate)
    with pytest.raises(InsightsError, match='same name'):
        metrics.collect(reset=True)

    assert Counter.objects.count() == before
    assert metrics.create_counters == []


def test_collect_command_exits_with_an_error_when_an_insight_fails(broken_insight):
    with pytest.raises(CommandError, match=r'1 of \d+ insights failed'):
        management.call_command('collect_insights')
    assert Counter.objects.filter(label='count_users').exists()


def test_an_app_keeps_its_uuid_when_the_insights_database_is_rebuilt(collected):
    before = dict(App.objects.values_list('module', 'uuid'))

    App.objects.all().delete()
    metrics.collect(reset=True)

    assert dict(App.objects.values_list('module', 'uuid')) == before
