# Installation

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

Each app can have it's own `insignts.py` file, these files are auto-discovered by Django Insights, so at any given location it would pick up your metrics.

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

### Settings

Add django_insights package, insights database and router to your settings

```python

INSTALLED_APPS = [
    ...
    "django_insights",
]


DATABASES = {
    ...
    "insights": {"ENGINE": "django.db.backends.sqlite3", "NAME": "db/insights.db"},
    ...
}

DATABASE_ROUTERS = ['django_insights.database.Router']

```

Note: please make sure you exclude the database in your `.gitignore` file

### Migrate database

```bash
workon myapp
python manage.py migrate insights --database=insights
```

### Collect your insights

```bash
python manage.py collect_insights
```

You now have a database containing all insights from your application.

You can inspect this database yourself with `sqlite3 db/insights.db` - or - you can use the Django Insights dashboard.
