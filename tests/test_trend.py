from datetime import datetime, timedelta
from typing import Any

import pytest
from django.template import Context, Template

from django_insights.metrics import collect_trend, metrics
from django_insights.models import Counter, Gauge
from django_insights.registry import registry
from django_insights.templatetags.insight_stat import trend

pytestmark = pytest.mark.django_db(databases=['default', 'insights'])


def series(*values):
    return lambda: [
        (datetime(2026, 1, 1) + timedelta(days=n), v) for n, v in enumerate(values)
    ]


def test_collect_trend_keeps_the_values_oldest_first():
    assert collect_trend(series(3, 5.5, 8)) == [3.0, 5.5, 8.0]


def test_collect_trend_sorts_the_points_by_time():
    rows = [
        (datetime(2026, 3, 1), 3),
        (datetime(2026, 1, 1), 1),
        (datetime(2026, 2, 1), 2),
    ]
    assert collect_trend(lambda: rows) == [1.0, 2.0, 3.0]


def test_collect_trend_skips_rows_without_a_value_or_a_time():
    rows: list[Any] = [
        (datetime(2026, 1, 1), 1),
        (datetime(2026, 2, 1), None),
        (None, 5),
        (datetime(2026, 3, 1), 3),
    ]
    assert collect_trend(lambda: rows) == [1.0, 3.0]


def test_collect_trend_is_empty_without_a_trend():
    assert collect_trend(None) == []


def test_collect_trend_keeps_the_latest_points_only():
    assert collect_trend(series(*range(100))) == [float(n) for n in range(40, 100)]


def test_a_counter_without_a_trend_has_an_empty_one(collected):
    assert Counter.objects.get(label='count_workspaces').trend == []


def test_collected_counters_and_gauges_get_their_trend(collected):
    assert len(Counter.objects.get(label='count_users').trend) > 1
    assert len(Gauge.objects.get(label='ai_share_of_messages').trend) > 1


def test_the_trend_is_rebuilt_by_every_collect(collected):
    before = Counter.objects.get(label='count_users').trend
    metrics.collect(reset=True)
    assert Counter.objects.get(label='count_users').trend == before


def test_a_failing_trend_is_reported_like_a_failing_insight(collected, monkeypatch):
    def broken():
        raise RuntimeError('no trend')

    @metrics.counter(question='q', trend=broken)
    def with_broken_trend() -> int:
        return 1

    failures = metrics.collect(reset=True)
    assert [f.label for f in failures] == ['with_broken_trend']
    assert Counter.objects.filter(label='count_users').exists()
    registry.registered_insights.pop()


@pytest.mark.parametrize(
    ('values', 'expected'),
    [([], None), ([5], None), ([0, 5], None), ([100, 110], 10.0), ([200, 100], -50.0)],
)
def test_trend_compares_the_last_two_values(values, expected):
    assert trend(values) == expected


def test_a_sparkline_needs_two_values():
    template = Template('{% load insight_stat %}{{ values|sparkline }}')
    assert template.render(Context({'values': [1.0]})) == ''
    assert '<polyline' in template.render(Context({'values': [1.0, 3.0, 2.0]}))
    assert '<polyline' in template.render(Context({'values': [4.0, 4.0, 4.0]}))
