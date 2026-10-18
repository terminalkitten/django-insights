from __future__ import annotations

from datetime import timedelta

from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F
from django.db.models.functions import TruncMonth

from django_insights.metrics import metrics
from django_insights.metrics_types import (
    BarChartResult,
    ScatterPlotResult,
    TimeSeriesResult,
)
from project.testapp.support.models import Ticket
from project.testapp.trends import monthly

label = "Support"

RESOLUTION = ExpressionWrapper(
    F('resolved_at') - F('created_at'), output_field=DurationField()
)
FIRST_RESPONSE = ExpressionWrapper(
    F('first_response_at') - F('created_at'), output_field=DurationField()
)
PRIORITIES = ['urgent', 'normal', 'low']


def hours(duration: timedelta | None) -> float:
    return round(duration.total_seconds() / 3600, 1) if duration else 0.0


@metrics.counter(
    question="How many tickets are still open?",
    trend=lambda: monthly(Ticket.objects, 'created_at'),
)
def count_open_tickets() -> int:
    return Ticket.objects.filter(resolved_at__isnull=True).count()


@metrics.gauge(
    question="How many hours until a ticket gets a first response?",
    desc="Average over all answered tickets",
)
def avg_first_response_hours() -> float:
    average = Ticket.objects.filter(first_response_at__isnull=False).aggregate(
        average=Avg(FIRST_RESPONSE)
    )
    return hours(average['average'])


@metrics.gauge(question="How many hours does it take to resolve a ticket?")
def avg_resolution_hours() -> float:
    average = Ticket.objects.filter(resolved_at__isnull=False).aggregate(
        average=Avg(RESOLUTION)
    )
    return hours(average['average'])


@metrics.gauge(
    question="How satisfied are the customers?",
    desc="Average score from 1 to 5, not every ticket is rated",
    trend=lambda: monthly(
        Ticket.objects.filter(satisfaction__isnull=False),
        'created_at',
        Avg('satisfaction'),
    ),
)
def csat_score() -> float:
    average = Ticket.objects.aggregate(average=Avg('satisfaction'))['average']
    return round(average or 0.0, 2)


@metrics.gauge(question="How many percent of the tickets are resolved?")
def resolved_share_of_tickets() -> float:
    total = Ticket.objects.count()
    if not total:
        return 0.0
    return round(
        100 * Ticket.objects.filter(resolved_at__isnull=False).count() / total, 1
    )


@metrics.timeseries(
    question="How many tickets are created per month?",
    xlabel="Month",
    xformat='%Y-%m',
    ylabel="Num of tickets",
)
def tickets_per_month() -> TimeSeriesResult:
    return (
        Ticket.objects.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Count('pk'))
        .values_list('month', 'total')
        .order_by('month')
    )


@metrics.timeseries(
    question="How does the satisfaction change over time?",
    xlabel="Month",
    xformat='%Y-%m',
    ylabel="Average score",
)
def csat_per_month() -> TimeSeriesResult:
    return (
        Ticket.objects.filter(satisfaction__isnull=False)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(score=Avg('satisfaction'))
        .values_list('month', 'score')
        .order_by('month')
    )


@metrics.barchart(
    question="Where do the tickets come from?",
    xlabel="Channel",
    ylabel="Num of tickets",
)
def tickets_by_channel() -> BarChartResult:
    return (
        Ticket.objects.values('channel')
        .annotate(total=Count('pk'))
        .annotate(tickets=F('total'))
        .order_by('-total')
        .values_list('total', 'tickets', 'channel')
    )


@metrics.barchart(
    question="What scores do customers give?",
    desc="Every score from 1 to 5, also the ones nobody gave",
    xlabel="Score",
    ylabel="Num of tickets",
)
def satisfaction_scores() -> BarChartResult:
    counts = dict(
        Ticket.objects.filter(satisfaction__isnull=False)
        .values('satisfaction')
        .annotate(total=Count('pk'))
        .values_list('satisfaction', 'total')
    )
    return [(counts.get(score, 0), 0, str(score)) for score in range(1, 6)]


@metrics.barchart(
    question="How long does it take to resolve a ticket, per priority?",
    xlabel="Priority",
    ylabel="Hours",
)
def resolution_hours_by_priority() -> BarChartResult:
    averages = dict(
        Ticket.objects.filter(resolved_at__isnull=False)
        .values('priority')
        .annotate(average=Avg(RESOLUTION))
        .values_list('priority', 'average')
    )
    return [
        (hours(averages.get(priority)), 0, priority)
        for priority in PRIORITIES
        if priority in averages
    ]


@metrics.hbarchart(
    question="Which workspaces have the most open tickets?",
    desc="Top 10 workspaces",
    xlabel="Workspace",
    ylabel="Num of open tickets",
)
def workspaces_with_most_open_tickets() -> BarChartResult:
    return (
        Ticket.objects.filter(resolved_at__isnull=True)
        .values('workspace__name')
        .annotate(total=Count('pk'))
        .annotate(share=F('total'))
        .order_by('-total', 'workspace__name')[:10]
        .values_list('total', 'share', 'workspace__name')
    )


@metrics.scatterplot(
    question="Does a quick first response mean a quick resolution?",
    desc="The 500 latest resolved tickets",
    xlabel="Hours to first response",
    ylabel="Hours to resolution",
)
def first_response_vs_resolution() -> ScatterPlotResult:
    rows = (
        Ticket.objects.filter(
            resolved_at__isnull=False, first_response_at__isnull=False
        )
        .order_by('-created_at')[:500]
        .annotate(response=FIRST_RESPONSE, resolution=RESOLUTION)
        .values_list('response', 'resolution', 'priority')
    )
    return [
        (hours(resolution), hours(response), priority)
        for response, resolution, priority in rows
    ]
