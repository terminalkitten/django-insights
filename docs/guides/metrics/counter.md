---
title: Counter
description: A whole number, such as how many orders, users or reports there are.
sidebar:
  order: 1
---

Use a counter when the answer is **how many**. It is shown as a number on the dashboard, optionally with a [trend](trend.md).

```python
from django_insights.metrics import metrics
from shop.models import Order


@metrics.counter(question="How many orders have been placed?")
def count_orders() -> int:
    return Order.objects.count()
```

- Return an `int`. The value is stored as a big integer.
- Counters of all apps are listed together on the dashboard.

## A window

The question decides what to count. A counter can look at a period, for example the last 30 days:

```python
from datetime import timedelta

from django.utils import timezone


@metrics.counter(question="How many orders were placed in the last 7 days?")
def orders_this_week() -> int:
    since = timezone.now() - timedelta(days=7)
    return Order.objects.filter(created_at__gte=since).count()
```

Add `trend=` to see how it moved over time, see [Trend](trend.md).
