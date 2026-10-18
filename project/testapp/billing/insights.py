from __future__ import annotations

from django.db.models import Count, F, Sum
from django.db.models.functions import TruncMonth

from django_insights.metrics import metrics
from django_insights.metrics_types import BarChartResult, TimeSeriesResult
from project.testapp.billing.models import Invoice, Subscription
from project.testapp.trends import monthly

label = "Billing"


@metrics.counter(question="How many paying subscriptions are active?")
def count_paying_subscriptions() -> int:
    return (
        Subscription.objects.filter(ended_at__isnull=True)
        .exclude(plan=Subscription.Plan.FREE)
        .count()
    )


@metrics.gauge(
    question="What is the monthly recurring revenue?",
    desc="Sum of the monthly price of all active subscriptions, in USD",
    trend=lambda: monthly(
        Invoice.objects.filter(status=Invoice.Status.PAID), 'issued_at', Sum('amount')
    ),
)
def monthly_recurring_revenue() -> float:
    total = Subscription.objects.filter(ended_at__isnull=True).aggregate(
        total=Sum('monthly_price')
    )['total']
    return float(total or 0)


@metrics.timeseries(
    question="How much revenue is paid per month?",
    xlabel="Month",
    xformat='%Y-%m',
    ylabel="Revenue in USD",
)
def revenue_per_month() -> TimeSeriesResult:
    return (
        Invoice.objects.filter(status=Invoice.Status.PAID)
        .annotate(month=TruncMonth('issued_at'))
        .values('month')
        .annotate(total=Sum('amount'))
        .values_list('month', 'total')
        .order_by('month')
    )


@metrics.timeseries(
    question="How many subscriptions end per month?",
    desc="Upgrades and cancellations",
    xlabel="Month",
    xformat='%Y-%m',
    ylabel="Num of subscriptions",
)
def subscriptions_ended_per_month() -> TimeSeriesResult:
    return (
        Subscription.objects.filter(ended_at__isnull=False)
        .annotate(month=TruncMonth('ended_at'))
        .values('month')
        .annotate(total=Count('pk'))
        .values_list('month', 'total')
        .order_by('month')
    )


@metrics.barchart(
    question="How are the active subscriptions spread over the plans?",
    xlabel="Plan",
    ylabel="Num of subscriptions",
)
def subscriptions_by_plan() -> BarChartResult:
    return (
        Subscription.objects.filter(ended_at__isnull=True)
        .values('plan')
        .annotate(total=Count('pk'))
        .annotate(subscriptions=F('total'))
        .order_by('-total')
        .values_list('total', 'subscriptions', 'plan')
    )


@metrics.barchart(
    question="Are the invoices paid?",
    xlabel="Status",
    ylabel="Num of invoices",
)
def invoices_by_status() -> BarChartResult:
    return (
        Invoice.objects.values('status')
        .annotate(total=Count('pk'))
        .annotate(invoices=F('total'))
        .order_by('-total')
        .values_list('total', 'invoices', 'status')
    )
