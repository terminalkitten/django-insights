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
