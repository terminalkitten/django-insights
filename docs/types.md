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
from django_insights.metrics import metrics
from django_insights.metrics_types import BarChartResult


@metrics.counter(question="How many authors are there?")
def count_authors() -> int:
    return Author.objects.count()


@metrics.barchart(
    question="Num of books by gender of author?", xlabel="Gender", ylabel="Num of books"
)
def books_by_gender() -> BarChartResult:
    return (
        Author.objects.values('gender')
        .annotate(n=Count('books'))
        .values_list('n', 'gender', 'name')
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
