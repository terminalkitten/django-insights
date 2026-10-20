---
title: Bar chart
description: A number per category, shown as vertical bars.
sidebar:
  order: 5
---

Use a bar chart to **compare a few categories**: orders per status, members per role, messages per weekday. For many categories or long names, use a [horizontal bar chart](hbarchart.md).

```python
from django.db.models import Count, F

from django_insights.metrics import metrics
from django_insights.metrics_types import BarChartResult
from shop.models import Order


@metrics.barchart(
    question="How are the orders doing?",
    desc="Orders by status",
    xlabel="Status",
    ylabel="Orders",
)
def orders_by_status() -> BarChartResult:
    return (
        Order.objects.values("status")
        .annotate(total=Count("pk"))
        .annotate(orders=F("total"))
        .order_by("-total")
        .values_list("total", "orders", "status")
    )
```

## Rows

Each row is `(height, unused, label)`.

- The first value is the height of the bar, the last one the label.
- The middle value is stored but not drawn. Pass any number, `0` is fine. When you build rows from a query it is easiest to annotate a copy of the total, as above, because `values_list("total", "total", ...)` with the same name twice collapses to one column on some Django versions.
- A `None` label is shown as an empty label.

## Keep empty categories

A category that has no rows is missing from a query. To always show all of them, build the rows yourself:

```python
from django.db.models.functions import ExtractWeekDay

WEEKDAYS = [
    (2, "Monday"),
    (3, "Tuesday"),
    (4, "Wednesday"),
    (5, "Thursday"),
    (6, "Friday"),
    (7, "Saturday"),
    (1, "Sunday"),
]


@metrics.barchart(
    question="On which weekday do people order?",
    xlabel="Weekday",
    ylabel="Orders",
)
def orders_by_weekday() -> BarChartResult:
    totals = dict(
        Order.objects.annotate(day=ExtractWeekDay("created_at"))
        .values("day")
        .annotate(total=Count("pk"))
        .values_list("day", "total")
    )
    return [(totals.get(day, 0), 0, name) for day, name in WEEKDAYS]
```
