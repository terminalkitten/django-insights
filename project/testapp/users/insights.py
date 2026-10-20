from __future__ import annotations

from datetime import timedelta

from django.db.models import Case, Count, F, Value, When
from django.db.models.functions import TruncMonth, TruncYear
from django.utils import timezone

from django_insights.metrics import metrics
from django_insights.metrics_types import BarChartResult, TimeSeriesResult
from project.testapp.trends import monthly
from project.testapp.users.models import AppUser

label = "Users"


@metrics.counter(
    question="How many users are there?",
    desc="Everybody that ever signed up, the trend shows the signups per month",
    trend=lambda: monthly(AppUser.objects, 'date_joined'),
)
def count_users() -> int:
    return AppUser.objects.count()


@metrics.gauge(question="How many percent of the users were invited?")
def invited_share_of_users() -> float:
    total = AppUser.objects.count()
    if not total:
        return 0.0
    return round(
        100 * AppUser.objects.filter(invited_by__isnull=False).count() / total, 1
    )


@metrics.timeseries(
    question="How many users were invited per year?",
    desc="Users that joined through an invitation of another user",
    xlabel="Year",
    xformat='%Y',
    ylabel="Num of users",
)
def users_invited_per_year() -> TimeSeriesResult:
    return (
        AppUser.objects.filter(invited_by__isnull=False)
        .annotate(year=TruncYear('date_joined'))
        .values('year')
        .annotate(total=Count('pk'))
        .values_list('year', 'total')
        .order_by('year')
    )


@metrics.barchart(
    question="How many users are active?",
    desc="Active and inactive users",
    xlabel="Status",
    ylabel="Num of users",
)
def active_vs_inactive_users() -> BarChartResult:
    return (
        AppUser.objects.annotate(
            status=Case(
                When(is_active=True, then=Value('Active')),
                default=Value('Inactive'),
            )
        )
        .values('status')
        .annotate(total=Count('pk'))
        .annotate(users=F('total'))
        .order_by('status')
        .values_list('total', 'users', 'status')
    )


@metrics.counter(question="How many users are active?")
def count_active_users() -> int:
    return AppUser.objects.filter(is_active=True).count()


@metrics.counter(
    question="How many users joined in the last 30 days?",
    trend=lambda: monthly(AppUser.objects, 'date_joined'),
)
def new_users_last_30_days() -> int:
    since = timezone.now() - timedelta(days=30)
    return AppUser.objects.filter(date_joined__gte=since).count()


@metrics.timeseries(
    question="How many users sign up per month?",
    xlabel="Month",
    xformat='%Y-%m',
    ylabel="Num of users",
)
def signups_per_month() -> TimeSeriesResult:
    return (
        AppUser.objects.annotate(month=TruncMonth('date_joined'))
        .values('month')
        .annotate(total=Count('pk'))
        .values_list('month', 'total')
        .order_by('month')
    )


@metrics.barchart(
    question="When were the users last seen?",
    xlabel="Last seen",
    ylabel="Num of users",
)
def users_by_last_seen() -> BarChartResult:
    now = timezone.now()
    week, month, quarter = (now - timedelta(days=days) for days in (7, 30, 90))
    seen = AppUser.objects.filter(last_login__isnull=False)
    return [
        (seen.filter(last_login__gte=week).count(), 0, 'Last 7 days'),
        (
            seen.filter(last_login__lt=week, last_login__gte=month).count(),
            0,
            '7-30 days',
        ),
        (
            seen.filter(last_login__lt=month, last_login__gte=quarter).count(),
            0,
            '30-90 days',
        ),
        (seen.filter(last_login__lt=quarter).count(), 0, 'Longer ago'),
        (AppUser.objects.filter(last_login__isnull=True).count(), 0, 'Never'),
    ]


@metrics.hbarchart(
    question="Who invited the most users?",
    desc="Top 10 users by the number of invitees",
    xlabel="User",
    ylabel="Num of invitees",
)
def top_inviters() -> BarChartResult:
    return (
        AppUser.objects.annotate(total=Count('invitees'))
        .filter(total__gt=0)
        .annotate(share=F('total'))
        .order_by('-total', 'email')[:10]
        .values_list('total', 'share', 'email')
    )
