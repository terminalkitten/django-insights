# Testing your insights

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

## Finding the insight

The `insights_query` fixture returns the insight named after the test, without `test_`. The `insights` marker is optional for that, it also registers the marker for `--strict-markers`.

| You want | Do this |
| --- | --- |
| the insight named after the test | `def test_count_authors(insights_query)` |
| another insight | `@pytest.mark.insights('count_authors')` |
| one of two insights with the same name | `@pytest.mark.insights('shop.insights.count_orders')` |

A name that does not exist, or that matches several insights, fails the test with a message that says which.

The insights are found in the `insights.py` file of every installed app. An error inside such a file is not hidden: importing it fails the test.
