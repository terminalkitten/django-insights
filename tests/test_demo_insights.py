from datetime import UTC, datetime, timedelta

import pytest
from django.db.models import Avg
from django.utils import timezone as tz

from django_insights.models import Bucket, BucketValue, Counter
from project.testapp.support import insights as support
from project.testapp.support.models import Ticket
from project.testapp.trends import months
from project.testapp.users.models import AppUser

pytestmark = pytest.mark.django_db(databases=['default', 'insights'])


def bucket_values(label):
    bucket = Bucket.objects.get(label=label)
    return list(BucketValue.objects.filter(bucket=bucket).order_by('pk'))


def test_months_lists_every_month_across_a_year_boundary():
    first = datetime(2025, 11, 17, 9, tzinfo=UTC)
    last = datetime(2026, 2, 3, tzinfo=UTC)

    assert months(first, last) == [
        datetime(2025, 11, 1, tzinfo=UTC),
        datetime(2025, 12, 1, tzinfo=UTC),
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 2, 1, tzinfo=UTC),
    ]


def test_every_score_is_listed_even_without_ratings():
    categories = [category for _, _, category in support.satisfaction_scores()]
    assert categories == ['1', '2', '3', '4', '5']


def test_the_backlog_ends_at_the_number_of_open_tasks(collected):
    backlog = bucket_values('open_tasks_over_time')
    open_tasks = Counter.objects.get(label='count_open_tasks').value

    assert backlog[-1].xvalue == open_tasks
    assert all(value.xvalue >= 0 for value in backlog)


def test_users_are_counted_in_exactly_one_last_seen_group(collected):
    groups = bucket_values('users_by_last_seen')
    assert sum(value.xvalue for value in groups) == AppUser.objects.count()


def test_the_support_demo_answers_urgent_tickets_faster(collected):
    def average_hours(priority):
        return support.hours(
            Ticket.objects.filter(
                priority=priority, first_response_at__isnull=False
            ).aggregate(average=Avg(support.FIRST_RESPONSE))['average']
        )

    assert average_hours('urgent') < average_hours('low')


def test_the_support_demo_never_resolves_a_ticket_before_it_was_created(collected):
    assert not Ticket.objects.filter(
        resolved_at__lt=tz.now() - timedelta(days=3650)
    ).exists()
    for ticket in Ticket.objects.filter(resolved_at__isnull=False)[:200]:
        assert ticket.resolved_at > ticket.created_at


def test_active_users_were_seen_more_recently_than_inactive_ones(collected):
    def average_age(active):
        users = AppUser.objects.filter(is_active=active, last_login__isnull=False)
        ages = [(tz.now() - user.last_login).days for user in users if user.last_login]
        return sum(ages) / len(ages)

    assert average_age(True) < average_age(False)
    assert not AppUser.objects.filter(
        last_login__lt=tz.now() - timedelta(days=5000)
    ).exists()
