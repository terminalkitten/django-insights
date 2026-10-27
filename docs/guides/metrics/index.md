---
title: Metrics
description: The six kinds of metrics, which one fits your question, and what they have in common.
sidebar:
  order: 1
---

A metric is a function in an `insights.py` file with a decorator that says what kind of answer it returns. Django Insights has six, from a single number to a chart.

## Which metric do I need?

| Your question looks like                                 | Use                    | Page                                 |
| -------------------------------------------------------- | ---------------------- | ------------------------------------ |
| "How many…?" A whole number                              | `@metrics.counter`     | [Counter](counter.md)                |
| "What is the average…?" A percentage, a ratio, a decimal | `@metrics.gauge`       | [Gauge](gauge.md)                    |
| "How many per day, week, month…?"                        | `@metrics.timeseries`  | [Time series](timeseries.md)         |
| "Does A depend on B?" Two numbers per item               | `@metrics.scatterplot` | [Scatter plot](scatterplot.md)       |
| "How many per category?" A few to a dozen categories     | `@metrics.barchart`    | [Bar chart](barchart.md)             |
| "Which are the top 10?" Many or long category names      | `@metrics.hbarchart`   | [Horizontal bar chart](hbarchart.md) |

Counters and gauges can also show a [trend](trend.md): a small line with the change against the previous period.

## Every metric

```python
from django_insights.metrics import metrics
from shop.models import Order


@metrics.counter(question="How many orders have been placed?")
def count_orders() -> int:
    return Order.objects.count()
```

- The function name is the **label** of the insight, unique per app. Keep it stable: it identifies the insight in the database and in your tests.
- `question` is shown on the dashboard. Write it as the question you want answered.
- `desc` is an optional line of explanation under it.
- The function runs your own queries on your own databases. It must only read.
- A function that raises is reported and skipped, the others still run. See [Collecting](../collecting.md).

## Options of the charts

The four chart types share these options, all optional:

| Option             | Does                                                              |
| ------------------ | ----------------------------------------------------------------- |
| `xlabel`, `ylabel` | the names of the axes                                             |
| `title`            | a title above the chart                                           |
| `xformat`          | how a timestamp is shown in the data table, `"%Y-%m"` for example |
| `yformat`          | stored with the chart, the dashboard does not use it yet          |

## What to return

The chart types return an iterable of tuples, a `QuerySet` from `values_list(...)` works. The position of each value matters:

| Type          | Row                                | Notes                                                                 |
| ------------- | ---------------------------------- | --------------------------------------------------------------------- |
| `timeseries`  | `(timestamp, value)`               | `timestamp` is a `datetime`, oldest first                             |
| `scatterplot` | `(vertical, horizontal, category)` | the first value is drawn on the vertical axis                         |
| `barchart`    | `(height, unused, label)`          | the second value is stored, but not drawn                             |
| `hbarchart`   | `(length, unused, label)`          | the length is shown behind the bar, labels over 30 characters are cut |

A missing label (`None`) is shown as an empty label. Annotate your functions with `TimeSeriesResult`, `ScatterPlotResult` and `BarChartResult` from `django_insights.metrics_types`.

:::tip
Not sure how to start? [Recipes](../recipes.md) has a complete insight for common questions.
:::
