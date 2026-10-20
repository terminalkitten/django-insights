---
title: Horizontal bar chart
description: A number per category as horizontal bars, for top lists and long names.
sidebar:
  order: 6
---

Use a horizontal bar chart for a **top 10** or when category names are long: customers, channels, URLs. The names read left to right and the value is printed behind each bar.

```python
from django.db.models import F, Sum

from django_insights.metrics import metrics
from django_insights.metrics_types import BarChartResult
from shop.models import Order


@metrics.hbarchart(
    question="Who are the top 5 customers?",
    desc="Total spent per customer",
    xlabel="Customer",
    ylabel="Spent in USD",
)
def best_customers() -> BarChartResult:
    return (
        Order.objects.filter(customer__isnull=False)
        .values("customer__username")
        .annotate(spent=Sum("total"))
        .annotate(orders=F("spent"))
        .order_by("-spent")[:5]
        .values_list("spent", "orders", "customer__username")
    )
```

## Rows

Each row is `(length, unused, label)`, the same as a [bar chart](barchart.md#rows).

- Sort and slice in the query: `.order_by("-spent")[:5]` gives a top 5. The chart shows the rows as you return them.
- Labels longer than 30 characters are cut with an ellipsis so they do not push the bars away. The full label is in the data table.

:::caution
A label is stored in the insights database. Use a username or an id instead of an email address when you share the file outside your team.
:::
