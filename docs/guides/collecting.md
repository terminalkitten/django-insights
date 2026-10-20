---
title: Collecting
description: How collect_insights runs, what happens when an insight fails, and running it from cron.
sidebar:
  order: 3
---

```bash
python manage.py collect_insights
```

All insights are collected in one transaction on the insights database: either everything is replaced, or nothing is. Your own databases are only read, by the queries you write in your insights.

## When an insight fails

An insight that raises an exception is logged (logger `django_insights.registry`, with the traceback) and reported, the other insights still run. A failed insight rolls back its own writes. The command prints every failed insight and exits with an error:

```text
1 of 14 insights failed
```

From code, `metrics.collect()` returns the list of failures. It raises `InsightsError` (from `django_insights.exceptions`) when an insight saves duplicates, and keeps the previous data.

## In production

Insights describe your data at the moment you collect, so run the command whenever the dashboard should update, for example every night from cron:

```text
0 3 * * * cd /srv/app && python manage.py collect_insights
```

The progress bar is hidden when the output is not a terminal, so the command is safe in cron and CI. A non-zero exit code means at least one insight failed: let your monitoring watch for it.

:::note
The insights database is a cache of your data. You can delete it at any time, migrate it again and run `collect_insights` to rebuild everything, trends included.
:::
