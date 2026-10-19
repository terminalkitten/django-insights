---
title: Dashboard
description: Show the collected insights in the built-in dashboard, in light and dark.
sidebar:
  order: 2
---

Include the URLs of Django Insights in your project:

```python
from django.urls import include, path

urlpatterns = [
    path("insights/", include("django_insights.urls", namespace="insights")),
]
```

Visit <http://localhost:8000/insights/> to see your insights. The dashboard requires a logged in user, to restrict it further see [Permissions](../reference/settings.md#permissions).

| Light | Dark |
| --- | --- |
| ![Dashboard, light](../img/dashboard-light.png) | ![Dashboard, dark](../img/dashboard-dark.png) |
| ![App, light](../img/app-light.png) | ![App, dark](../img/app-dark.png) |

Every visitor can switch between light and dark, `INSIGHTS_DEFAULT_THEME` sets the starting mode. The colors and style come from [Theming](../guides/theming.md).

The stylesheets, icons and the Geist font are served from the package, nothing is loaded from a CDN. Run `collectstatic` as usual.

## Chart cache

Charts are rendered with matplotlib on every request. To keep them as files instead, turn the cache on:

```python
INSIGHTS_CHARTS_USE_MEDIA_CACHE = True
INSIGHTS_MEDIA_CACHE_ROOT = BASE_DIR / "media/insights"
```

Cached images are written atomically, and only cached chart images (`*-*-*.png`) in that folder are ever deleted.
