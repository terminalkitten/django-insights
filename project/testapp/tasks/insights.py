from __future__ import annotations

from django.db.models import Count, F
from django.db.models.functions import TruncMonth

from django_insights.metrics import metrics
from django_insights.metrics_types import BarChartResult, TimeSeriesResult
from project.testapp.tasks.models import Project, Task
from project.testapp.trends import monthly

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
