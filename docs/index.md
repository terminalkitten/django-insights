---
title: Django Insights
description: Answer questions about your Django app with numbers and charts, written as small functions next to your code.
---

::image[Django Insights, questions about your app as numbers and charts]{src="img/banner.png"}

How many people signed up this month? Which weekday do customers order? Is the refund rate going up? **Django Insights** answers questions like these straight from your own database, with a function per question, right next to the code it is about.

```python
# shop/insights.py
from django_insights.metrics import metrics
from shop.models import Order


@metrics.counter(question="How many orders have been placed?")
def count_orders() -> int:
    return Order.objects.count()
```

Run `python manage.py collect_insights` and the answer shows up in a dashboard, and in a SQLite file you can query or share.

## What can you do with it?

::::cards
:::card[Track the numbers that matter]{href="guides/recipes.md"}
Signups, active users, revenue, refund rate. A counter or a gauge, with a trend line.
:::

:::card[See how things change]{href="guides/metrics/index.md"}
Time series, bar charts and scatter plots from the queries you already know.
:::

:::card[Share without exporting data]{href="reference/database.md"}
Hand out one SQLite file with answers instead of CSV files with customer data.
:::

:::card[Test your queries]{href="guides/testing.md"}
Every insight is a plain function, so the pytest plugin tests it against your test database.
:::
::::

## How it works

:::steps
1. **Write** an `insights.py` in any of your apps. Each function is one question, and returns a number or the rows of a chart.
2. **Collect** with `python manage.py collect_insights`, by hand or from cron. Django Insights runs every function against your database, and stores the answers in a separate SQLite database.
3. **Look** at the built-in dashboard in your browser, or query the SQLite file from a script, a notebook or `sqlite3`.
:::

Your own database is only ever read, by the queries you write. The answers are a cache: delete the insights database at any time and `collect_insights` rebuilds it, trends included.

## Is it for you?

It is a good fit when you want insights about the **current state** of your app that you can gather again at any moment: counts per day, averages, shares, top 10 lists. It is not a realtime source: no requests per second, no live counters. More in [About](reference/about.md).

## Start in five minutes

::::tabs{sync="pkg"}
:::tab[pip]
`pip install django-insights`
:::

:::tab[uv]
`uv add django-insights`
:::
::::

Then follow [Getting started](getting-started/index.md): you have your first insight in the dashboard in a few steps.

:::note[v2 is in the works]
A new major release lives on the `main` branch: Django 5.2+ and Python 3.11+, a refreshed dashboard and many fixes. These docs describe the `main` branch and may change before the release. Upgrading from 0.2? Read [Migrating to v2](guides/migrating.md).
:::

Supported: Django 5.2 (LTS), 6.0 and 6.1 (Django 6 needs Python 3.12+), on Python 3.11 to 3.14.
