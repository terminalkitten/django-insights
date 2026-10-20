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

:::note[Login]
A visitor who is not logged in is sent to your `LOGIN_URL`, which is `/accounts/login/` by default. If your project has no login page there, point it to one, for example the admin:

```python
LOGIN_URL = "/admin/login/"
```
:::

## The dashboard

All counters and gauges of all apps, with their trend. The sidebar lists your apps.

::::tabs{sync="mode"}
:::tab[Light]
::image[The dashboard with counters and gauges, light]{src="../img/dashboard-light.png" caption="Counters and gauges of all apps."}
:::

:::tab[Dark]
::image[The dashboard with counters and gauges, dark]{src="../img/dashboard-dark.png" caption="The same page in dark mode."}
:::
::::

## An app

Every app with an `insights.py` has its own page with the charts, each with the data behind it.

::::tabs{sync="mode"}
:::tab[Light]
::image[The page of an app with its charts, light]{src="../img/app-light.png" caption="Charts of one app, click one for the data."}
:::

:::tab[Dark]
::image[The page of an app with its charts, dark]{src="../img/app-dark.png" caption="The same page in dark mode."}
:::
::::

Every visitor can switch between light and dark, `INSIGHTS_DEFAULT_THEME` sets the starting mode. The colors and style come from [Theming](../guides/theming.md).

The stylesheets, icons and the Geist font are served from the package, nothing is loaded from a CDN. Run `collectstatic` as usual. The dashboard needs a browser with `<dialog>` and Tailwind 4 support: Chrome 111+, Safari 16.4+ or Firefox 128+. To change the page itself, see [Customizing](../guides/customizing.md).

## Chart cache

Charts are rendered with matplotlib on every request. To keep them as files instead, turn the cache on:

```python
INSIGHTS_CHARTS_USE_MEDIA_CACHE = True
INSIGHTS_MEDIA_CACHE_ROOT = BASE_DIR / "media/insights"
```

Cached images are written atomically, and only cached chart images (`*-*-*.png`) in that folder are ever deleted.
