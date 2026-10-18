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

Each app can have it's own `insights.py` file, these files are auto-discovered by Django Insights, so at any given location it would pick up your metrics.

In these insights files you write out any metric you would like to track. Each metric starts with a question and some values to store. Below is a example of the `@metrics.counter` function:

```python
# project/testapp/insights.py
from django_insights.metrics import metrics
from project.testapp.models import Message

label = "Workspace"


@metrics.counter(question="How many messages have been sent?")
def count_messages() -> int:
    return Message.objects.count()
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

Run `python manage.py check` to verify the configuration, it warns about a missing insights database or router. All options are listed on the [settings](settings.md) page.

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

Note: You need to run the `python manage.py collect_insights` command each time you want to update data on your dashboard. In production, you can setup a cron job to call this command at regular intervals depending on your use case. 


You can inspect this database yourself with `sqlite3 db/insights.db` - or - you can use the Django Insights dashboard.

### PDF export

The report at `/pdf/` needs PyMuPDF, install it with the `pdf` extra:

```bash
pip install 'django-insights[pdf]'
```

Note: PyMuPDF is licensed under the AGPL-3.0 (a commercial license is available from Artifex), so it is optional. Without it everything else works and `/pdf/` raises an error that says what to install. It has no system dependencies. Its layout engine only supports basic CSS, the report is styled by `insights/css/pdf.css`.
