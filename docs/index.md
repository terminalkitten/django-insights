---
title: Django Insights
description: Create insights for your Django app, written right next to your application logic.
---

::image[Django Insights, questions about your app as numbers and charts]{src="img/banner.png"}

Django Insights turns questions about your app into numbers and charts. You write each insight as a small function next to your application code, `collect_insights` runs them all and stores the answers in a separate SQLite database, and a built-in dashboard shows them.

```python
# project/testapp/insights.py
from django_insights.metrics import metrics
from project.testapp.models import Message

label = "Workspace"


@metrics.counter(question="How many messages have been sent?")
def count_messages() -> int:
    return Message.objects.count()
```

:::note[v2 is in the works]
A new major release lives on the `feat/v2` branch: Django 5.2+ and Python 3.11+, a refreshed dashboard and many fixes. These docs describe that branch and may change before the release. Upgrading from 0.2? Read [Migrating to v2](guides/migrating.md).
:::

::::cards
:::card[Get started]{href="getting-started/index.md"}
Install the app, add the insights database and collect your first insights.
:::

:::card[Metrics]{href="guides/metrics.md"}
Counters, gauges, time series, scatter plots and bar charts, with trends.
:::

:::card[Theming]{href="guides/theming.md"}
Basecoat styles and shadcn/ui colors, shared by the dashboard and the charts.
:::

:::card[Settings]{href="reference/settings.md"}
Every setting with its default, and the system checks that guard them.
:::
::::

## Supported versions

- Django 5.2 (LTS), 6.0 and 6.1 (Django 6 needs Python 3.12+)
- Python 3.11 to 3.14

## Why

Insights are gathered from the current state of your app, so they can be rebuilt from your own data at any moment. A SQLite file of insights can be shared on request instead of spreading CSV exports with possibly sensitive data. Read [About](reference/about.md) for the background and when Django Insights is (not) the right tool.
