---
title: Getting started
description: Install Django Insights, add the insights database and collect your first insights.
sidebar:
  order: 1
---

:::steps
1. Install the package:

   ```bash
   pip install django-insights
   ```

2. Add the app, the insights database and the router to your settings:

   ```python
   INSTALLED_APPS = [
       ...
       "django_insights",
   ]

   DATABASES = {
       ...
       "insights": {
           "ENGINE": "django.db.backends.sqlite3",
           "NAME": BASE_DIR / "db/insights.db",
       },
   }

   DATABASE_ROUTERS = ["django_insights.database.Router"]
   ```

   Keep the database out of git: add `db/insights.db` to your `.gitignore`.

3. Create the tables in the insights database:

   ```bash
   python manage.py migrate insights --database=insights
   ```

4. Write an `insights.py` in one of your apps (see below).

5. Collect:

   ```bash
   python manage.py collect_insights
   ```
:::

## Your first insight

Each app can have its own `insights.py`. These files are discovered automatically, wherever the app lives:

```text
project
└── testapp
    └── insights.py
```

Every insight starts with a question and returns a value:

```python
# project/testapp/insights.py
from django_insights.metrics import metrics
from project.testapp.models import Message

label = "Workspace"


@metrics.counter(question="How many messages have been sent?")
def count_messages() -> int:
    return Message.objects.count()
```

The optional module-level `label` names the app in the dashboard, and is stored in the `insights_app` table.

After `collect_insights` you have a database with all insights of your app. Inspect it yourself with `sqlite3 db/insights.db`, or open the [dashboard](dashboard.md).

:::tip
Run `python manage.py check` after changing the settings. It warns about a missing insights database or router, see [System checks](../reference/checks.md).
:::

## Keep it up to date

`collect_insights` reads your data at that moment. Run it each time you want fresh numbers, in production for example from a cron job. More in [Collecting](../guides/collecting.md).
