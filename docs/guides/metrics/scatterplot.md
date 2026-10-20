---
title: Scatter plot
description: Pairs of values, to see if one number goes with another.
sidebar:
  order: 4
---

Use a scatter plot to see whether **two numbers go together**: order size and price, tokens and cost, members and messages. One dot per item.

```python
from django_insights.metrics import metrics
from django_insights.metrics_types import ScatterPlotResult
from shop.models import Order


@metrics.scatterplot(
    question="Do bigger orders contain more items?",
    xlabel="Items",
    ylabel="Order total in USD",
)
def total_vs_items() -> ScatterPlotResult:
    return Order.objects.values_list("total", "quantity", "status")[:200]
```

## Rows

Each row is `(vertical, horizontal, category)`.

- The **first** value is drawn on the vertical axis, the second on the horizontal axis. Mind the order: it is the other way around from `x, y`.
- The third value is a name for the dot, shown in the data table.
- Cap the rows with a slice. A few hundred dots show a pattern, tens of thousands only make a blob. Order first, so you always get the same ones, for example the latest: `.order_by("-created_at")[:500]`.
