---
title: The insights database
description: The tables of the insights SQLite database and how to query them yourself.
sidebar:
  order: 3
---

`collect_insights` rebuilds the `insights` database from your own data. It is a normal SQLite file, so you can read it with anything that speaks SQL. Here are the tables.

| Table                  | One row per                  | Main columns                                                                                     |
| ---------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------ |
| `insights_app`         | module with an `insights.py` | `uuid`, `module`, `label`                                                                        |
| `insights_counter`     | counter                      | `app_id`, `label`, `question`, `desc`, `value`, `trend`, `created_at`                            |
| `insights_gauge`       | gauge                        | the same as a counter, `value` is a decimal number                                               |
| `insights_bucket`      | chart                        | `app_id`, `label`, `question`, `desc`, `type`, `xlabel`, `xformat`, `ylabel`, `yformat`, `title` |
| `insights_bucketvalue` | point or bar of a chart      | `bucket_id`, `timestamp`, `xvalue`, `yvalue`, `category`                                         |

- The `label` is the name of your function and is unique per app, so two apps can both have a `count_users`.
- The `uuid` of an app is derived from its module path, so a dashboard URL stays the same when you rebuild the database.
- `type` of a bucket is `1` for a time series, `3` for a scatter plot, `4` for a bar chart and `5` for a horizontal bar chart.
- `trend` is a JSON list with the latest 60 values of the trend, empty without a `trend=` function.
- In `insights_bucketvalue` the `timestamp` is only filled for a time series, and a bucket has at most one value per timestamp.

## Querying

```bash
sqlite3 db/insights.db "
  select a.label, c.label, c.value
  from insights_counter c join insights_app a on a.uuid = c.app_id
"
```

```text
Shop|count_orders|40
```

The values of a chart:

```bash
sqlite3 db/insights.db "
  select category, xvalue from insights_bucketvalue v
  join insights_bucket b on b.id = v.bucket_id
  where b.label = 'by_status' order by xvalue desc
"
```

From Python, the standard library is enough:

```python
import sqlite3

with sqlite3.connect("db/insights.db") as db:
    for label, value in db.execute("select label, value from insights_counter"):
        print(label, value)
```

Or use the models of Django Insights from a shell of your project, they live on the `insights` database:

```python
from django_insights.models import Counter

Counter.objects.get(label="count_orders").value
```

## Sharing

The file holds answers, not your data: counts, averages and the points of the charts. That is what makes it safe to share on request. Check what your insights return before you hand it out, a `category` can be an email address if you group by one.
