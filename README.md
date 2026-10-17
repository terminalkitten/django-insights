[![CI](https://github.com/terminalkitten/django-insights/actions/workflows/main.yml/badge.svg)](https://github.com/terminalkitten/django-insights/actions/workflows/main.yml)

!["Django Insights"](https://raw.githubusercontent.com/terminalkitten/django-insights/main/docs/assets/images/banner.png)

> [!NOTE]
> **v2 is in the works.** We are currently working on a new major release on the `feat/v2` branch: Django 5.2+ and Python 3.11+, a refreshed dashboard, optional PDF export and a lot of fixes. The documentation below describes the current state of that branch and may change before release.

## Features

Create insights for your app, store them in a SQLite database for further processing, these insights are written right next to your application logic.

### Note:

Still working on some small things, extending tests and improving the documentation.

For now focus is on:

- Django 5.2 (LTS), 6.0 and 6.1;
- Python 3.11 – 3.14

## Installation

Installing with:

```bash
pip install 'django-insights'
```

## Usage

First create a `insights.py` file in your app directory, for example:

```bash
project
└── testapp
    └── insights.py
```

Each app can have it's own `insights.py` file, these files are auto-discovered by Django Insights, so at any given location it would pick up your metrics.

In these insights files you write out any metric you would like to track. Each metric starts with a question and some values to store. Below is a example of the `@metrics.counter` function:

```python
# project/testapp/insights.py
from django_insights.metrics import metrics
from project.testapp.models import Author

label = "Bookstore"


@metrics.counter(question="How many authors are there?")
def count_authors() -> int:
    return Author.objects.count()
```

Insight apps can have a `label`, this is used in the dashboard or can be read from `insights_app` table later on.

### Configure Django

Add django_insights package, insights database and router to your settings

```python

INSTALLED_APPS = [
    ...
    "django_insights",
]


DATABASES = {
    ...
    "insights": {
            "ENGINE": "django.db.backends.sqlite3", 
            "NAME": os.path.join(BASE_DIR,"db/insights.db")
        },
    ...
}

DATABASE_ROUTERS = ['django_insights.database.Router']

```

Note: please make sure you exclude the database in your `.gitignore` file

Migrate insights database:

```bash
workon myapp
python manage.py migrate insights --database=insights
```

Now collect your insights

```bash
python manage.py collect_insights
```

You now have a database containing all insights from your application.

Note: You need to run the `python manage.py collect_insights` command each time you want to update data on your dashboard. In production, you can setup a cron job to call this command at regular intervals depending on your use case. 

You can inspect this database yourself with `sqlite3 db/insights.db` - or - you can use the Django Insights dashboard.

### Dashboard

!["Dashboard - Main Screen"](https://raw.githubusercontent.com/terminalkitten/django-insights/main/docs/assets/images/screen_1.png)

To enable this dashboard, add the following settings:

```python
from django.urls import include, path

urlpatterns = [
    path(
        'insights/',
        include('django_insights.urls', namespace='insights'),
    ),
]
```

!["Dashboard - App"](https://raw.githubusercontent.com/terminalkitten/django-insights/main/docs/assets/images/screen_2.png)

Now you can visit http://localhost:8000/insights/ to inspect your Django Insights database.

### PDF report

The dashboard has a PDF report at `insights/pdf/`. It needs PyMuPDF, which is optional:

```bash
pip install 'django-insights[pdf]'
```

PyMuPDF is licensed under the AGPL-3.0 (a commercial license is available from Artifex), so it is not installed by default. Without it everything else works and the report explains what to install.

## Metrics

Django Insights collects six types of metrics, each one is a decorator for a function in an `insights.py` file:

- `@metrics.counter`: a whole number, `-> int`
- `@metrics.gauge`: a decimal number, `-> float`
- `@metrics.timeseries`: values over time, shown as a line chart
- `@metrics.scatterplot`: pairs of values, shown as a scatter plot
- `@metrics.barchart`: values per category, shown as a bar chart
- `@metrics.hbarchart`: values per category, shown as a horizontal bar chart

Every decorator takes a `question` and optionally a `desc`. The chart types also take `xlabel`, `ylabel`, `xformat`, `yformat` and `title`. The functions run your own queries, a `QuerySet` can be returned as is.

### Counter:

```python
from django_insights.metrics import metrics
from project.testapp.models import Author


@metrics.counter(question="How many authors are there?")
def count_authors() -> int:
    return Author.objects.count()
```

### Gauge:

```python
from django.db.models import Avg, Count

from django_insights.metrics import metrics
from project.testapp.models import Author


@metrics.gauge(question="Average book(s) per author?")
def avg_books_per_author() -> float:
    avg_total_books = (
        Author.objects.prefetch_related('books')
        .annotate(total_books=Count('books'))
        .aggregate(Avg('total_books'))
        .get('total_books__avg')
    )

    return avg_total_books or 0.0
```

### Timeseries:

```python
from django.db.models import Count
from django.db.models.functions import TruncMonth

from django_insights.metrics import metrics
from django_insights.metrics_types import TimeSeriesResult
from project.testapp.models import Book


@metrics.timeseries(
    question="Num of books created per month?",
    desc="How many books are added each month, since the opening of our store",
    xlabel="Month",
    xformat='%m',
    ylabel="Num of books",
)
def num_of_books_per_month() -> TimeSeriesResult:
    return (
        Book.objects.all()
        .annotate(month=TruncMonth('created'))
        .values('month')
        .filter(month__isnull=False)
        .annotate(total=Count('pk'))
        .values_list('month', 'total')
        .order_by('month')
    )
```

### Scatterplot:

```python
from django.db.models import Count, Value

from django_insights.metrics import metrics
from django_insights.metrics_types import ScatterPlotResult
from project.testapp.models import Author


@metrics.scatterplot(
    question="Num of books by age of author?",
    xlabel="Age",
    ylabel="Num of books",
)
def author_age_vs_num_of_books() -> ScatterPlotResult:
    return (
        Author.objects.values('age')
        .annotate(num_of_books=Count('books'), category=Value("author"))
        .values_list('num_of_books', 'age', 'category')
    )
```

### Barchart:

```python
from django.db.models import Case, Count, Value, When

from django_insights.metrics import metrics
from django_insights.metrics_types import BarChartResult
from project.testapp.models import Author


@metrics.barchart(
    question="Num of books by gender of author?",
    xlabel="Gender",
    ylabel="Num of books",
)
def author_gender_vs_num_of_books() -> BarChartResult:
    return (
        Author.objects.values('gender')
        .annotate(
            num_of_books=Count('books'),
            gender_category=Case(
                When(gender=1, then=Value('Male')),
                When(gender=2, then=Value('Female')),
            ),
        )
        .values_list('num_of_books', 'gender', 'gender_category')
    )
```

### Horizontal barchart:

```python
from django.db.models import Count, F

from django_insights.metrics import metrics
from django_insights.metrics_types import BarChartResult
from project.testapp.models import Author


@metrics.hbarchart(
    question="Which authors have the most books?",
    xlabel="Author",
    ylabel="Num of books",
)
def top_authors_by_num_of_books() -> BarChartResult:
    return (
        Author.objects.annotate(num_of_books=Count('books'))
        .annotate(total=F('num_of_books'))
        .order_by('-num_of_books', 'name')[:10]
        .values_list('num_of_books', 'total', 'name')
    )
```

### What to return

Return an iterable of tuples, a `QuerySet` from `values_list(...)` works. The position of each value matters:

| Type | Row | Notes |
| --- | --- | --- |
| `timeseries` | `(timestamp, value)` | `timestamp` is a `datetime`, `xformat` formats the timestamp in the table |
| `scatterplot` | `(vertical, horizontal, category)` | the first value is drawn on the vertical axis |
| `barchart` | `(height, unused, label)` | the second value is stored, but not drawn |
| `hbarchart` | `(length, number, label)` | `number` is shown behind the label, as `label..:number` |

A missing label (`None`) is shown as an empty label. Use the result types `TimeSeriesResult`, `ScatterPlotResult` and `BarChartResult` from `django_insights.metrics_types` to annotate the functions.

## Collecting

```bash
python manage.py collect_insights
```

All insights are collected in one transaction on the insights database: either everything is replaced, or nothing is. Your own databases are only read by the queries you write in your insights.

When an insight raises an exception it is logged (logger `django_insights.registry`) and reported, the other insights still run. The command prints every failed insight and exits with an error, for example `1 of 14 insights failed`. The progress bar is hidden when the output is not a terminal, so it is safe in cron.

Run `python manage.py check` after changing the settings below, it warns about a missing insights database, a missing router, an invalid permission or a renamed setting. These checks only warn, they never stop your project from starting.

## Settings

All settings are optional and read from your Django settings.

| Setting | Default | Description |
| --- | --- | --- |
| `INSIGHTS_APP_NAME` | `"MyApp"` | Name shown in the dashboard |
| `INSIGHTS_DEFAULT_THEME` | `"dark"` | `"light"` or `"dark"`, used until a visitor chooses a theme |
| `INSIGHTS_CHART_DPI` | `180` | Resolution of the chart images |
| `INSIGHTS_CHART_LIGHT_PRIMARY_COLOR` | `"#2563EB"` | Chart color in the light theme |
| `INSIGHTS_CHART_DARK_PRIMARY_COLOR` | `"#BFDBFE"` | Chart color in the dark theme |
| `INSIGHTS_CHARTS_USE_MEDIA_CACHE` | `False` | Keep rendered charts as files instead of rendering them on every request |
| `INSIGHTS_MEDIA_CACHE_ROOT` | `None` | Directory for the cached charts, required when the cache is on. Only cached chart images in it are deleted |
| `INSIGHTS_DASHBOARD_PERMISSIONS` | `None` | List of permission classes, see below |

The dashboard always requires a logged in user. To restrict it further, add permission classes, every class must return `True`:

```python
class IsStaff:
    def has_permission(self, request):
        return request.user.is_staff


INSIGHTS_DASHBOARD_PERMISSIONS = [IsStaff]
```

A class without a `has_permission` method denies access, it never grants it.

Version 2 renamed `INSIGHT_CHARTS_USE_MEDIA_CACHE`, `INSIGHT_MEDIA_CACHE_ROOT` and `INSIGHT_DASHBOARD_PERMISSIONS` to the `INSIGHTS_` prefix. The old names are ignored, `manage.py check` warns when they are still set.

## Testing your insights

The pytest plugin comes with Django Insights, there is nothing to configure. It gives a test the plain function behind an insight, so you can test your queries against the test database. Nothing is saved.

```python
import pytest
from django.utils import timezone

from project.testapp.models import Author


@pytest.mark.insights
@pytest.mark.django_db
def test_count_authors(insights_query):
    Author.objects.create(created=timezone.now(), name='Ada', age=36, gender=1)

    assert insights_query() == 1
```

The insight is found by the name of the test without `test_`. To choose another one, give the marker a name: `@pytest.mark.insights('count_authors')`. When two apps have an insight with the same name, use `module.name`, for example `'shop.insights.count_orders'`. A name that does not exist fails the test with a message.

## Use-cases

Insights are gathered from your current application state, Django Insights is not intentend to be used as a realtime, incremementing data-source. You should be able to re-gather these insights from your actual data at any moment in time.

Yes:

- How many users, how many users invited a year
- How many reports a day, how many messages send on Wednesday's

No:

- How many GET request for url XXX a second
- Realtime profit target percentage

## Background

I'm currently working at a small company that is in the process of renewing some parts of our product. To gain insight into the usage over different periods, we have tried a few solutions. We initially attempted to periodically generate CSV files from queries, as well as send data to a dashboard at regular intervals.

We ended up with many exports that where spread out over multiple people. Additionally, exporting data directly from the database also posed a security risk, as it required constant movement of possible sensitive information. After several months of working with CSV files, which were often outdated and required conversion by other (paid) tools, we where looking for a better solution.

I wanted an easy-to-configure file within our various apps that would allow me to create "insights" easily, so Django Insights was born. I decided to switch to a local SQLite database which could be share on request, as a plus these files can be tracked by a security officer.

## Ideas

- Connect to other datasources and export to different file-formats ( ArrowFile?, NDJSON )

## Is it any good?

[Yes.](http://news.ycombinator.com/item?id=3067434)

## License

The MIT License
