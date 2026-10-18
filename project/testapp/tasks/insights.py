from __future__ import annotations

from datetime import timedelta

from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F
from django.db.models.functions import ExtractWeekDay, TruncMonth
from django.utils import timezone

from django_insights.metrics import metrics
from django_insights.metrics_types import BarChartResult, TimeSeriesResult
from project.testapp.insights import WEEKDAYS
from project.testapp.tasks.models import Project, Task
from project.testapp.trends import monthly, months

label = "Tasks"


@metrics.counter(
    question="How many tasks are open?",
    trend=lambda: monthly(Task.objects, 'created_at'),
)
def count_open_tasks() -> int:
    return Task.objects.filter(completed_at__isnull=True).count()


@metrics.gauge(question="How many percent of the tasks are completed?")
def completed_share_of_tasks() -> float:
    total = Task.objects.count()
    if not total:
        return 0.0
    return round(
        100 * Task.objects.filter(completed_at__isnull=False).count() / total, 1
    )


@metrics.gauge(question="How many days does it take to complete a task?")
def avg_days_to_complete() -> float:
    durations = Task.objects.filter(completed_at__isnull=False).values_list(
        'created_at', 'completed_at'
    )
    days = [(done - created).total_seconds() / 86400 for created, done in durations]
    return round(sum(days) / len(days), 1) if days else 0.0


@metrics.timeseries(
    question="How many tasks are created per month?",
    xlabel="Month",
    xformat='%Y-%m',
    ylabel="Num of tasks",
)
def tasks_created_per_month() -> TimeSeriesResult:
    return (
        Task.objects.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Count('pk'))
        .values_list('month', 'total')
        .order_by('month')
    )


@metrics.timeseries(
    question="How many tasks are completed per month?",
    xlabel="Month",
    xformat='%Y-%m',
    ylabel="Num of tasks",
)
def tasks_completed_per_month() -> TimeSeriesResult:
    return (
        Task.objects.filter(completed_at__isnull=False)
        .annotate(month=TruncMonth('completed_at'))
        .values('month')
        .annotate(total=Count('pk'))
        .values_list('month', 'total')
        .order_by('month')
    )


@metrics.barchart(
    question="How many tasks are still open per priority?",
    xlabel="Priority",
    ylabel="Num of open tasks",
)
def open_tasks_by_priority() -> BarChartResult:
    return (
        Task.objects.filter(completed_at__isnull=True)
        .values('priority')
        .annotate(total=Count('pk'))
        .annotate(tasks=F('total'))
        .order_by('-total')
        .values_list('total', 'tasks', 'priority')
    )


@metrics.hbarchart(
    question="Which projects have the most open tasks?",
    desc="Top 10 projects",
    xlabel="Project",
    ylabel="Num of open tasks",
)
def top_projects_by_open_tasks() -> BarChartResult:
    return (
        Project.objects.filter(tasks__completed_at__isnull=True)
        .annotate(total=Count('tasks'))
        .annotate(open=F('total'))
        .order_by('-total', 'name')[:10]
        .values_list('total', 'open', 'name')
    )


@metrics.counter(question="How many high priority tasks are open?")
def count_high_priority_open_tasks() -> int:
    return Task.objects.filter(
        completed_at__isnull=True, priority=Task.Priority.HIGH
    ).count()


@metrics.gauge(question="How many percent of the tasks are done within a week?")
def completed_within_a_week_share() -> float:
    total = Task.objects.count()
    if not total:
        return 0.0
    quick = Task.objects.filter(
        completed_at__lte=F('created_at') + timedelta(days=7)
    ).count()
    return round(100 * quick / total, 1)


@metrics.barchart(
    question="How many days does a task take, per priority?",
    desc="Average days from created to completed",
    xlabel="Priority",
    ylabel="Days",
)
def days_to_complete_by_priority() -> BarChartResult:
    duration = ExpressionWrapper(
        F('completed_at') - F('created_at'), output_field=DurationField()
    )
    averages = dict(
        Task.objects.filter(completed_at__isnull=False)
        .values('priority')
        .annotate(average=Avg(duration))
        .values_list('priority', 'average')
    )
    return [
        (round(averages[priority].total_seconds() / 86400, 1), 0, priority)
        for priority in ('high', 'medium', 'low')
        if priority in averages
    ]


@metrics.barchart(
    question="On which weekday are tasks created?",
    xlabel="Weekday",
    ylabel="Num of tasks",
)
def tasks_by_weekday() -> BarChartResult:
    totals = dict(
        Task.objects.annotate(day=ExtractWeekDay('created_at'))
        .values('day')
        .annotate(total=Count('pk'))
        .values_list('day', 'total')
    )
    return [(totals.get(day, 0), 0, name) for day, name in WEEKDAYS]


@metrics.timeseries(
    question="How big is the backlog over time?",
    desc="Open tasks at the end of each month",
    xlabel="Month",
    xformat='%Y-%m',
    ylabel="Num of open tasks",
)
def open_tasks_over_time() -> TimeSeriesResult:
    created = dict(
        Task.objects.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Count('pk'))
        .values_list('month', 'total')
    )
    completed = dict(
        Task.objects.filter(completed_at__isnull=False)
        .annotate(month=TruncMonth('completed_at'))
        .values('month')
        .annotate(total=Count('pk'))
        .values_list('month', 'total')
    )
    if not created:
        return []

    backlog, series = 0, []
    for month in months(min(created), timezone.now()):
        backlog += created.get(month, 0) - completed.get(month, 0)
        series.append((month, backlog))
    return series


@metrics.hbarchart(
    question="Who creates the most tasks?",
    desc="Top 10 users",
    xlabel="User",
    ylabel="Num of tasks",
)
def top_task_creators() -> BarChartResult:
    return (
        Task.objects.filter(created_by__isnull=False)
        .values('created_by__email')
        .annotate(total=Count('pk'))
        .annotate(share=F('total'))
        .order_by('-total', 'created_by__email')[:10]
        .values_list('total', 'share', 'created_by__email')
    )
