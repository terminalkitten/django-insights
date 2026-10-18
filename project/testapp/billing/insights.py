from __future__ import annotations

from django.db.models import Count, F, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from django_insights.metrics import metrics
from django_insights.metrics_types import BarChartResult, TimeSeriesResult
from project.testapp.billing.models import Invoice, Subscription
from project.testapp.trends import monthly, months

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
    trend=lambda: monthly(Invoice.objects, 'issued_at', Sum('amount')),
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


@metrics.counter(question="How many invoices are overdue?")
def count_overdue_invoices() -> int:
    return Invoice.objects.filter(status=Invoice.Status.OVERDUE).count()


@metrics.gauge(
    question="What is the average revenue per paying workspace?",
    desc="Monthly recurring revenue divided by the paying subscriptions, in USD",
)
def average_revenue_per_workspace() -> float:
    paying = Subscription.objects.filter(ended_at__isnull=True).exclude(
        plan=Subscription.Plan.FREE
    )
    total = paying.aggregate(total=Sum('monthly_price'))['total']
    count = paying.count()
    return round(float(total or 0) / count, 2) if count else 0.0


@metrics.gauge(question="How many percent of the invoices are overdue?")
def overdue_share_of_invoices() -> float:
    total = Invoice.objects.count()
    if not total:
        return 0.0
    overdue = Invoice.objects.filter(status=Invoice.Status.OVERDUE).count()
    return round(100 * overdue / total, 1)


@metrics.timeseries(
    question="How many paying subscriptions are active per month?",
    desc="Counted on the first day of each month",
    xlabel="Month",
    xformat='%Y-%m',
    ylabel="Num of subscriptions",
)
def paying_subscriptions_per_month() -> TimeSeriesResult:
    paying = list(
        Subscription.objects.exclude(plan=Subscription.Plan.FREE).values_list(
            'started_at', 'ended_at'
        )
    )
    if not paying:
        return []
    first = min(started for started, _ in paying)
    return [
        (
            month,
            sum(
                started <= month and (ended is None or ended > month)
                for started, ended in paying
            ),
        )
        for month in months(first, timezone.now())
    ]


@metrics.barchart(
    question="What does each plan bring in?",
    desc="Paid invoices per plan, in USD",
    xlabel="Plan",
    ylabel="Revenue in USD",
)
def revenue_by_plan() -> BarChartResult:
    return (
        Invoice.objects.filter(status=Invoice.Status.PAID)
        .values('subscription__plan')
        .annotate(total=Sum('amount'))
        .annotate(share=F('total'))
        .order_by('-total')
        .values_list('total', 'share', 'subscription__plan')
    )
