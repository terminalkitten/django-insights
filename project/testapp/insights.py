from __future__ import annotations

from datetime import timedelta

from django.db.models import Avg, Case, Count, F, FloatField, Sum, Value, When
from django.db.models.functions import (
    Concat,
    ExtractHour,
    ExtractWeekDay,
    TruncDay,
    TruncMonth,
)
from django.utils import timezone

from django_insights.metrics import metrics
from django_insights.metrics_types import (
    BarChartResult,
    ScatterPlotResult,
    TimeSeriesResult,
)
from project.testapp.models import Channel, Membership, Message, Report, Workspace
from project.testapp.trends import monthly

label = "Workspace"

WEEKDAYS = [
    (2, 'Monday'),
    (3, 'Tuesday'),
    (4, 'Wednesday'),
    (5, 'Thursday'),
    (6, 'Friday'),
    (7, 'Saturday'),
    (1, 'Sunday'),
]


@metrics.counter(question="How many workspaces are there?")
def count_workspaces() -> int:
    return Workspace.objects.count()


@metrics.counter(
    question="How many messages have been sent?",
    desc="Messages of people and of the AI assistant, the trend shows the messages per month",
    trend=lambda: monthly(Message.objects, 'created_at'),
)
def count_messages() -> int:
    return Message.objects.count()


@metrics.counter(
    question="How many reports have been created?",
    trend=lambda: monthly(Report.objects, 'created_at'),
)
def count_reports() -> int:
    return Report.objects.count()


@metrics.gauge(question="Average members per workspace?")
def avg_members_per_workspace() -> float:
    average = Workspace.objects.annotate(total=Count('memberships')).aggregate(
        Avg('total')
    )
    return average['total__avg'] or 0.0


@metrics.gauge(
    question="How many percent of the messages are written by the AI assistant?",
    trend=lambda: monthly(
        Message.objects,
        'created_at',
        Avg(Case(When(is_ai=True, then=1.0), default=0.0, output_field=FloatField()))
        * 100,
    ),
)
def ai_share_of_messages() -> float:
    total = Message.objects.count()
    if not total:
        return 0.0
    return round(100 * Message.objects.filter(is_ai=True).count() / total, 1)


@metrics.barchart(
    question="Which weekday do people write the most messages?",
    desc="Messages per weekday, busy from Tuesday to Thursday",
    xlabel="Weekday",
    ylabel="Num of messages",
)
def messages_per_weekday() -> BarChartResult:
    totals = dict(
        Message.objects.annotate(day=ExtractWeekDay('created_at'))
        .values('day')
        .annotate(total=Count('pk'))
        .values_list('day', 'total')
    )
    return [(totals.get(day, 0), 0, name) for day, name in WEEKDAYS]


@metrics.timeseries(
    question="How big is the share of messages written by the AI assistant?",
    desc="Percentage of the messages per month",
    xlabel="Month",
    xformat='%Y-%m',
    ylabel="Percentage of messages",
)
def ai_share_per_month() -> TimeSeriesResult:
    ai = Case(When(is_ai=True, then=1.0), default=0.0, output_field=FloatField())
    return (
        Message.objects.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(share=Avg(ai) * 100)
        .values_list('month', 'share')
        .order_by('month')
    )


@metrics.timeseries(
    question="What does the AI assistant cost per month?",
    xlabel="Month",
    xformat='%Y-%m',
    ylabel="Cost in USD",
)
def ai_cost_per_month() -> TimeSeriesResult:
    return (
        Message.objects.filter(is_ai=True)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('cost'))
        .values_list('month', 'total')
        .order_by('month')
    )


@metrics.barchart(
    question="What does each AI model cost?",
    xlabel="Model",
    ylabel="Cost in USD",
)
def ai_cost_per_model() -> BarChartResult:
    return (
        Message.objects.filter(is_ai=True)
        .values('model')
        .annotate(total=Sum('cost'), messages=Count('pk'))
        .order_by('-total')
        .values_list('total', 'messages', 'model')
    )


@metrics.scatterplot(
    question="What does a message of the AI assistant cost for its length?",
    desc="The 500 latest messages of the AI assistant, a model has its own price per token",
    xlabel="Tokens",
    ylabel="Cost in USD",
)
def ai_cost_vs_tokens() -> ScatterPlotResult:
    return (
        Message.objects.filter(is_ai=True)
        .order_by('-created_at', '-pk')[:500]
        .values_list('cost', 'tokens', 'model')
    )


@metrics.timeseries(
    question="How many reports are created per day?",
    desc="The last 90 days",
    xlabel="Day",
    xformat='%Y-%m-%d',
    ylabel="Num of reports",
)
def reports_per_day() -> TimeSeriesResult:
    since = timezone.now() - timedelta(days=90)
    return (
        Report.objects.filter(created_at__gte=since)
        .annotate(day=TruncDay('created_at'))
        .values('day')
        .annotate(total=Count('pk'))
        .values_list('day', 'total')
        .order_by('day')
    )


@metrics.barchart(
    question="How are the reports doing?",
    desc="Reports by status",
    xlabel="Status",
    ylabel="Num of reports",
)
def reports_by_status() -> BarChartResult:
    return (
        Report.objects.values('status')
        .annotate(total=Count('pk'))
        .annotate(reports=F('total'))
        .order_by('-total')
        .values_list('total', 'reports', 'status')
    )


@metrics.hbarchart(
    question="Which channels are the busiest?",
    desc="Top 10 channels by number of messages",
    xlabel="Channel",
    ylabel="Num of messages",
)
def top_channels_by_messages() -> BarChartResult:
    return (
        Channel.objects.annotate(total=Count('messages'))
        .annotate(share=F('total'))
        .annotate(title=Concat(F('workspace__name'), Value(' #'), F('name')))
        .order_by('-total', 'title')[:10]
        .values_list('total', 'share', 'title')
    )


@metrics.counter(
    question="How many channels are there?",
    desc="Public and private channels of all workspaces",
)
def count_channels() -> int:
    return Channel.objects.count()


@metrics.gauge(
    question="How many tokens does an answer of the AI assistant use?",
    desc="Average over all answers",
)
def avg_tokens_per_ai_message() -> float:
    average = Message.objects.filter(is_ai=True).aggregate(average=Avg('tokens'))
    return round(average['average'] or 0.0, 1)


@metrics.timeseries(
    question="How many messages are sent per month?",
    xlabel="Month",
    xformat='%Y-%m',
    ylabel="Num of messages",
)
def messages_per_month() -> TimeSeriesResult:
    return (
        Message.objects.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Count('pk'))
        .values_list('month', 'total')
        .order_by('month')
    )


@metrics.barchart(
    question="At what hour of the day do people write?",
    desc="Messages per hour of the day, in UTC",
    xlabel="Hour",
    ylabel="Num of messages",
)
def messages_per_hour() -> BarChartResult:
    totals = dict(
        Message.objects.annotate(hour=ExtractHour('created_at'))
        .values('hour')
        .annotate(total=Count('pk'))
        .values_list('hour', 'total')
    )
    return [(totals.get(hour, 0), 0, f'{hour:02d}') for hour in range(24)]


@metrics.barchart(
    question="Do people talk in private channels?",
    xlabel="Channel",
    ylabel="Num of messages",
)
def messages_by_visibility() -> BarChartResult:
    totals = dict(
        Message.objects.values('channel__is_private')
        .annotate(total=Count('pk'))
        .values_list('channel__is_private', 'total')
    )
    return [
        (totals.get(private, 0), 0, 'Private' if private else 'Public')
        for private in (False, True)
    ]


@metrics.barchart(
    question="Who has which role?",
    desc="Memberships per role",
    xlabel="Role",
    ylabel="Num of members",
)
def members_by_role() -> BarChartResult:
    return (
        Membership.objects.values('role')
        .annotate(total=Count('pk'))
        .annotate(members=F('total'))
        .order_by('-total')
        .values_list('total', 'members', 'role')
    )


@metrics.hbarchart(
    question="Which workspaces are the busiest?",
    desc="Messages per workspace",
    xlabel="Workspace",
    ylabel="Num of messages",
)
def workspaces_by_messages() -> BarChartResult:
    return (
        Message.objects.values('channel__workspace__name')
        .annotate(total=Count('pk'))
        .annotate(share=F('total'))
        .order_by('-total', 'channel__workspace__name')[:10]
        .values_list('total', 'share', 'channel__workspace__name')
    )


@metrics.scatterplot(
    question="Do bigger workspaces send more messages?",
    desc="One dot per workspace",
    xlabel="Messages",
    ylabel="Members",
)
def members_vs_messages() -> ScatterPlotResult:
    members = dict(
        Membership.objects.values('workspace')
        .annotate(total=Count('pk'))
        .values_list('workspace', 'total')
    )
    messages = dict(
        Message.objects.values('channel__workspace')
        .annotate(total=Count('pk'))
        .values_list('channel__workspace', 'total')
    )
    names = dict(Workspace.objects.values_list('pk', 'name'))
    return [
        (members.get(pk, 0), messages.get(pk, 0), name) for pk, name in names.items()
    ]
