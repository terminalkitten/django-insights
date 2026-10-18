# Metrics

Django Insights collects six types of metrics. Each one is a decorator for a function in an `insights.py` file, the function runs your own queries. A `QuerySet` can be returned as is.

| Decorator | Returns | Shown as |
| --- | --- | --- |
| `@metrics.counter` | `int` | number |
| `@metrics.gauge` | `float` | number |
| `@metrics.timeseries` | `TimeSeriesResult` | line chart |
| `@metrics.scatterplot` | `ScatterPlotResult` | scatter plot |
| `@metrics.barchart` | `BarChartResult` | bar chart |
| `@metrics.hbarchart` | `BarChartResult` | horizontal bar chart |

Every decorator takes a `question` and optionally a `desc`. The chart types also take `xlabel`, `ylabel`, `xformat`, `yformat` and `title`.

```python
from django.db.models import Count, F

from django_insights.metrics import metrics
from django_insights.metrics_types import BarChartResult
from project.testapp.models import Message, Report


@metrics.counter(question="How many messages have been sent?")
def count_messages() -> int:
    return Message.objects.count()


@metrics.barchart(
    question="How are the reports doing?", xlabel="Status", ylabel="Num of reports"
)
def reports_by_status() -> BarChartResult:
    return (
        Report.objects.values('status')
        .annotate(total=Count('pk'))
        .annotate(reports=F('total'))
        .values_list('total', 'reports', 'status')
    )
```

## What to return

Return an iterable of tuples. The position of each value matters:

| Type | Row | Notes |
| --- | --- | --- |
| `timeseries` | `(timestamp, value)` | `timestamp` is a `datetime`, `xformat` formats the timestamp in the table |
| `scatterplot` | `(vertical, horizontal, category)` | the first value is drawn on the vertical axis |
| `barchart` | `(height, unused, label)` | the second value is stored, but not drawn |
| `hbarchart` | `(length, number, label)` | `number` is shown behind the label, as `label..:number` |

A missing label (`None`) is shown as an empty label.

## Failing insights

When an insight raises an exception it is logged and reported, the other insights still run. `collect_insights` prints every failed insight and exits with an error. All insights are saved in one transaction on the insights database.

## Trend

A counter or gauge can show a trend: a small line and the change of the last point against the one before it. Give it a `trend` function that returns a time series, the same rows a `timeseries` insight returns:

```python
from django.db.models import Count
from django.db.models.functions import TruncMonth


def signups_per_month():
    return (
        AppUser.objects.annotate(month=TruncMonth('date_joined'))
        .values('month')
        .annotate(total=Count('pk'))
        .values_list('month', 'total')
        .order_by('month')
    )


@metrics.counter(question="How many users are there?", trend=signups_per_month)
def count_users() -> int:
    return AppUser.objects.count()
```

The trend is read from your own data on every collect and stored with the counter, so it is rebuilt together with everything else and nothing needs a backup. The latest 60 points are kept. The trend describes what its query returns, not the value itself: the example shows the signups per month next to the total number of users. Leave out the running month, it is not complete yet and shows as a drop.
