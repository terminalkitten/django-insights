---
title: Testing insights
description: Test the queries behind your insights with the pytest plugin.
sidebar:
  order: 5
---

The pytest plugin comes with Django Insights, there is nothing to configure. It gives a test the plain function behind an insight, so you can test your queries against the test database. Nothing is saved.

```python
import pytest
from django.utils import timezone

from project.testapp.models import Channel, Message, Workspace


@pytest.mark.insights
@pytest.mark.django_db
def test_count_messages(insights_query):
    workspace = Workspace.objects.create(name="Acme", created_at=timezone.now())
    channel = Channel.objects.create(
        workspace=workspace, name="general", created_at=timezone.now()
    )
    Message.objects.create(channel=channel, created_at=timezone.now())

    assert insights_query() == 1
```

## Finding the insight

The insight is found by the name of the test without `test_`: `test_count_messages` gets `count_messages`. To choose another one, give the marker a name:

```python
@pytest.mark.insights("count_messages")
```

When two apps have an insight with the same name, use `module.name`, for example `"shop.insights.count_orders"`. A name that does not exist, or matches more than one insight, fails the test with a message.

:::note
The plugin loads through the `pytest11` entry point and does nothing at import, so it does not need Django to be configured. The `insights` marker is registered, `--strict-markers` works.
:::
