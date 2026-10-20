---
title: Gauge
description: A decimal number, such as an average, a ratio or a percentage.
sidebar:
  order: 2
---

Use a gauge when the answer is a **decimal**: an average, a percentage, a ratio. It is shown as a number on the dashboard, optionally with a [trend](trend.md).

```python
from django.db.models import Avg

from django_insights.metrics import metrics
from shop.models import Order


@metrics.gauge(question="What is the average order total?")
def average_order_total() -> float:
    return Order.objects.aggregate(Avg("total"))["total__avg"] or 0.0
```

- Return a `float`. `Avg` of an empty table is `None`, so end with `or 0.0`.

## A percentage

Divide yourself, and guard against an empty table:

```python
@metrics.gauge(question="What percentage of the orders is shipped?")
def shipped_share() -> float:
    total = Order.objects.count()
    if not total:
        return 0.0
    return round(100 * Order.objects.filter(status="shipped").count() / total, 1)
```
