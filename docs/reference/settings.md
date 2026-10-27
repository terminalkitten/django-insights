---
title: Settings
description: Every Django Insights setting with its default.
sidebar:
  order: 1
---

All settings are optional and read from your Django settings when they are used, so `override_settings` works in tests.

| Setting                           | Default   | Description                                                                                                |
| --------------------------------- | --------- | ---------------------------------------------------------------------------------------------------------- |
| `INSIGHTS_APP_NAME`               | `"MyApp"` | Name shown in the dashboard                                                                                |
| `INSIGHTS_DEFAULT_THEME`          | `"dark"`  | `"light"` or `"dark"`, used until a visitor chooses a theme                                                |
| `INSIGHTS_CHART_DPI`              | `180`     | Resolution of the chart images                                                                             |
| `INSIGHTS_STYLE`                  | `"vega"`  | Basecoat style: `vega`, `nova`, `maia`, `lyra`, `mira`, `luma`, `sera` or `rhea`                           |
| `INSIGHTS_THEME`                  | `None`    | A shadcn theme name like `"blue"`, or a dict with your own colors, see [Theming](../guides/theming.md)     |
| `INSIGHTS_CHARTS_USE_MEDIA_CACHE` | `False`   | Keep rendered charts as files instead of rendering them on every request                                   |
| `INSIGHTS_MEDIA_CACHE_ROOT`       | `None`    | Directory for the cached charts, required when the cache is on. Only cached chart images in it are deleted |
| `INSIGHTS_DASHBOARD_PERMISSIONS`  | `None`    | List of permission classes, see below                                                                      |

## Permissions

The dashboard always requires a logged in user. To restrict it further, add permission classes. Every class must return `True`:

```python
class IsStaff:
    def has_permission(self, request):
        return request.user.is_staff


INSIGHTS_DASHBOARD_PERMISSIONS = [IsStaff]
```

:::caution
A class without a `has_permission` method denies access, it never grants it.
:::

## Renamed in 0.3

Version 0.3 renamed `INSIGHT_CHARTS_USE_MEDIA_CACHE`, `INSIGHT_MEDIA_CACHE_ROOT` and `INSIGHT_DASHBOARD_PERMISSIONS` to the `INSIGHTS_` prefix, and replaced `INSIGHTS_CHART_LIGHT_PRIMARY_COLOR` and `INSIGHTS_CHART_DARK_PRIMARY_COLOR` with `INSIGHTS_THEME`. The old names are ignored, `manage.py check` warns when they are still set. See [Upgrading from 0.2](../guides/migrating.md).
