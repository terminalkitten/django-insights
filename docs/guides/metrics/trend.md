---
title: Trend
description: A small line and the change against the previous period, for counters and gauges.
sidebar:
  order: 7
---

A counter or gauge shows one number. A **trend** adds how it moved: a small line, and the change of the last point against the one before it.

Give the metric a `trend` function that returns a time series, the same rows a [time series](timeseries.md) insight returns:

```python
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import TruncMonth

from django_insights.metrics import metrics

User = get_user_model()


def signups_per_month():
    return (
        User.objects.annotate(month=TruncMonth("date_joined"))
        .values("month")
        .annotate(total=Count("pk"))
        .values_list("month", "total")
        .order_by("month")
    )


@metrics.counter(question="How many users are there?", trend=signups_per_month)
def count_users() -> int:
    return User.objects.count()
```

It works the same for a [gauge](gauge.md).

## What the trend describes

The trend is **what its query returns**, not the value itself. The example shows the signups per month next to the total number of users, so the line and the number answer two related questions. For a gauge such as a refund rate, return the rate per month, see [Recipes](../recipes.md#is-the-refund-rate-going-up).

- The trend is read from your own data on every collect and stored with the metric. It is rebuilt together with everything else, so nothing needs a backup.
- The latest 60 points are kept.
- Rows without a value are skipped, and fewer than two points show no line.
- Leave out the running month: it is not complete yet and shows as a drop. Filter it away in the query, for example with `created_at__lt=start_of_this_month`.
