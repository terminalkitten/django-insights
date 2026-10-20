import datetime

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from django_insights.models import App, Bucket, BucketValue, Counter

pytestmark = pytest.mark.django_db(databases=['default', 'insights'])


def test_the_same_label_can_exist_in_different_apps():
    first = App.objects.create(module='first.insights')
    second = App.objects.create(module='second.insights')
    Counter.objects.create(app=first, label='total')
    Counter.objects.create(app=second, label='total')
    assert Counter.objects.filter(label='total').count() == 2


def test_a_label_is_unique_within_an_app():
    app = App.objects.create(module='first.insights')
    Counter.objects.create(app=app, label='total')
    with pytest.raises(IntegrityError), transaction.atomic(using='insights'):
        Counter.objects.create(app=app, label='total')


def test_counters_hold_values_beyond_32_bits():
    app = App.objects.create(module='first.insights')
    counter = Counter.objects.create(app=app, label='big', value=3_000_000_000)
    counter.refresh_from_db()
    assert counter.value == 3_000_000_000


def test_bucket_values_are_ordered_by_timestamp():
    app = App.objects.create(module='first.insights')
    bucket = Bucket.objects.create(app=app, label='series')
    now = timezone.now()
    for offset in (3, 1, 2):
        BucketValue.objects.create(
            bucket=bucket,
            timestamp=now + datetime.timedelta(days=offset),
            xvalue=offset,
        )
    assert [value.xvalue for value in bucket.values.all()] == [1, 2, 3]


def test_values_without_timestamp_keep_insertion_order():
    app = App.objects.create(module='first.insights')
    bucket = Bucket.objects.create(app=app, label='bars')
    for name in ('b', 'a', 'c'):
        BucketValue.objects.create(bucket=bucket, category=name)
    assert [value.category for value in bucket.values.all()] == ['b', 'a', 'c']


def test_apps_and_metrics_have_a_stable_order():
    for module in ('z.insights', 'a.insights'):
        App.objects.create(module=module)
    assert [app.module for app in App.objects.all()] == ['a.insights', 'z.insights']
