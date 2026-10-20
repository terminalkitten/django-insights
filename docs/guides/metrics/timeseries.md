---
title: Time series
description: Values over time, shown as a line chart.
sidebar:
  order: 3
---

Use a time series for **how something changes**: per day, week or month. It is a line chart, with the data in a table behind it.

```python
from django.db.models import Sum
from django.db.models.functions import TruncMonth

from django_insights.metrics import metrics
from django_insights.metrics_types import TimeSeriesResult
from shop.models import Order


@metrics.timeseries(
    question="What is the revenue per month?",
    xlabel="Month",
    xformat="%Y-%m",
    ylabel="Revenue in USD",
)
def revenue_per_month() -> TimeSeriesResult:
    return (
        Order.objects.annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Sum("total"))
        .values_list("month", "total")
        .order_by("month")
    )
```

## Rows

Each row is `(timestamp, value)`, with a `datetime`. Order by the timestamp: a line chart draws the rows in the order you return them.

- A time series has at most **one value per timestamp**. Group in the query, with `TruncDay`, `TruncWeek` or `TruncMonth`, so you do not return two rows for the same moment. Otherwise collecting fails and names the insight.
- Periods without data are not in the query result, so they are missing from the line. That is fine for most questions.
- `xformat` only changes how the timestamp reads in the data table.

## Other periods

```python
from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDay
from django.utils import timezone


@metrics.timeseries(
    question="How many orders are placed per day?",
    desc="The last 90 days",
    xlabel="Day",
    xformat="%Y-%m-%d",
    ylabel="Orders",
)
def orders_per_day() -> TimeSeriesResult:
    since = timezone.now() - timedelta(days=90)
    return (
        Order.objects.filter(created_at__gte=since)
        .annotate(day=TruncDay("created_at"))
        .values("day")
        .annotate(total=Count("pk"))
        .values_list("day", "total")
        .order_by("day")
    )
```
