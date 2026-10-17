from __future__ import annotations

from django.db.models import Case, Count, F, Value, When
from django.db.models.functions import TruncYear

from django_insights.metrics import metrics
from django_insights.metrics_types import BarChartResult, TimeSeriesResult
from project.testapp.users.models import AppUser

label = "Users"


@metrics.counter(
    question="How many users are there?",
    desc="Everybody that ever signed up",
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
