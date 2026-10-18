from __future__ import annotations

from django.db.models import Count, Expression, Manager, QuerySet
from django.db.models.functions import TruncMonth
from django.utils import timezone

from django_insights.metrics_types import TimeSeriesResult


def monthly(
    queryset: Manager | QuerySet,
    field: str,
    aggregate: Expression | None = None,
    months: int = 12,
) -> TimeSeriesResult:
    """Full months only, the running month is partial and would show as a drop"""
    end = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    number = end.year * 12 + end.month - 1 - months
    start = end.replace(year=number // 12, month=number % 12 + 1)
    return (
        queryset.filter(**{f'{field}__gte': start, f'{field}__lt': end})
        .annotate(month=TruncMonth(field))
        .values('month')
        .annotate(total=aggregate or Count('pk'))
        .values_list('month', 'total')
        .order_by('month')
    )
