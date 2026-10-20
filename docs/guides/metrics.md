---
title: Metrics
description: The six metric types, what each one returns, and trends for counters and gauges.
sidebar:
  order: 1
---

Django Insights collects six types of metrics. Each one is a decorator for a function in an `insights.py` file:

| Decorator              | Returns                      | Shown as               |
| ---------------------- | ---------------------------- | ---------------------- |
| `@metrics.counter`     | a whole number, `-> int`     | a number               |
| `@metrics.gauge`       | a decimal number, `-> float` | a number               |
| `@metrics.timeseries`  | values over time             | a line chart           |
| `@metrics.scatterplot` | pairs of values              | a scatter plot         |
| `@metrics.barchart`    | values per category          | a bar chart            |
| `@metrics.hbarchart`   | values per category          | a horizontal bar chart |

Every decorator takes a `question` and optionally a `desc`. The chart types also take `xlabel`, `ylabel`, `xformat`, `yformat` and `title`. The functions run your own queries, a `QuerySet` can be returned as is.

## Counter

```python
from django_insights.metrics import metrics
from project.testapp.models import Message


@metrics.counter(question="How many messages have been sent?")
def count_messages() -> int:
    return Message.objects.count()
```

## Gauge

```python
from django.db.models import Avg, Count

from django_insights.metrics import metrics
from project.testapp.models import Workspace


@metrics.gauge(question="Average members per workspace?")
def avg_members_per_workspace() -> float:
    average = Workspace.objects.annotate(total=Count("memberships")).aggregate(
        Avg("total")
    )
    return average["total__avg"] or 0.0
```

## Time series

```python
from django.db.models import Sum
from django.db.models.functions import TruncMonth

from django_insights.metrics import metrics
from django_insights.metrics_types import TimeSeriesResult
from project.testapp.models import Message


@metrics.timeseries(
    question="What does the AI assistant cost per month?",
    xlabel="Month",
    xformat="%Y-%m",
    ylabel="Cost in USD",
)
def ai_cost_per_month() -> TimeSeriesResult:
    return (
        Message.objects.filter(is_ai=True)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Sum("cost"))
        .values_list("month", "total")
        .order_by("month")
    )
```

## Scatter plot

```python
from django_insights.metrics import metrics
from django_insights.metrics_types import ScatterPlotResult
from project.testapp.models import Message


@metrics.scatterplot(
    question="What does a message of the AI assistant cost for its length?",
    xlabel="Tokens",
    ylabel="Cost in USD",
)
def ai_cost_vs_tokens() -> ScatterPlotResult:
    return (
        Message.objects.filter(is_ai=True)
        .order_by("-created_at", "-pk")[:500]
        .values_list("cost", "tokens", "model")
    )
```

## Bar chart

```python
from django.db.models import Count, F

from django_insights.metrics import metrics
from django_insights.metrics_types import BarChartResult
from project.testapp.models import Report


@metrics.barchart(
    question="How are the reports doing?",
    xlabel="Status",
    ylabel="Num of reports",
)
def reports_by_status() -> BarChartResult:
    return (
        Report.objects.values("status")
        .annotate(total=Count("pk"))
        .annotate(reports=F("total"))
        .values_list("total", "reports", "status")
    )
```

## Horizontal bar chart

```python
from django.db.models import Count, F

from django_insights.metrics import metrics
from django_insights.metrics_types import BarChartResult
from project.testapp.models import Channel


@metrics.hbarchart(
    question="Which channels are the busiest?",
    xlabel="Channel",
    ylabel="Num of messages",
)
def top_channels_by_messages() -> BarChartResult:
    return (
        Channel.objects.annotate(total=Count("messages"))
        .annotate(share=F("total"))
        .order_by("-total", "name")[:10]
        .values_list("total", "share", "name")
    )
```

## What to return

The chart types return an iterable of tuples, a `QuerySet` from `values_list(...)` works. The position of each value matters:

| Type          | Row                                | Notes                                                                 |
| ------------- | ---------------------------------- | --------------------------------------------------------------------- |
| `timeseries`  | `(timestamp, value)`               | `timestamp` is a `datetime`, `xformat` formats it in the table        |
| `scatterplot` | `(vertical, horizontal, category)` | the first value is drawn on the vertical axis                         |
| `barchart`    | `(height, unused, label)`          | the second value is stored, but not drawn                             |
| `hbarchart`   | `(length, unused, label)`          | the length is shown behind the bar, labels over 30 characters are cut |

A missing label (`None`) is shown as an empty label. Annotate your functions with `TimeSeriesResult`, `ScatterPlotResult` and `BarChartResult` from `django_insights.metrics_types`.

## Trend

A counter or gauge can show a trend: a small line and the change of the last point against the one before it. Give it a `trend` function that returns a time series, the same rows a `timeseries` insight returns:

```python
from django.db.models import Count
from django.db.models.functions import TruncMonth


def signups_per_month():
    return (
        AppUser.objects.annotate(month=TruncMonth("date_joined"))
        .values("month")
        .annotate(total=Count("pk"))
        .values_list("month", "total")
        .order_by("month")
    )


@metrics.counter(question="How many users are there?", trend=signups_per_month)
def count_users() -> int:
    return AppUser.objects.count()
```

The trend is read from your own data on every collect and stored with the counter, so it is rebuilt together with everything else and nothing needs a backup. The latest 60 points are kept.

:::tip
The trend describes what its query returns, not the value itself: the example shows the signups per month next to the total number of users. Leave out the running month, it is not complete yet and shows as a drop.
:::
