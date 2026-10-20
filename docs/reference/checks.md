---
title: System checks
description: The warnings manage.py check gives for the Django Insights settings.
sidebar:
  order: 2
---

Run `python manage.py check` after changing the settings. These checks only warn, they never stop your project from starting.

| Id              | Warns when                                                                                                         |
| --------------- | ------------------------------------------------------------------------------------------------------------------ |
| `insights.W001` | `INSIGHTS_DASHBOARD_PERMISSIONS` is not a list or tuple                                                            |
| `insights.W002` | a permission is not a class with a `has_permission(request)` method; the dashboard denies access until it is fixed |
| `insights.W003` | the chart cache is on, but `INSIGHTS_MEDIA_CACHE_ROOT` is not set                                                  |
| `insights.W004` | `DATABASES` has no `insights` entry                                                                                |
| `insights.W005` | `django_insights.database.Router` is not in `DATABASE_ROUTERS`                                                     |
| `insights.W006` | a setting still uses its old `INSIGHT_` name, which is ignored                                                     |
| `insights.W007` | `INSIGHTS_STYLE` is not a known style; `vega` is used                                                              |
| `insights.W008` | the `base` or `accent` of `INSIGHTS_THEME` is not known                                                            |
| `insights.W009` | `INSIGHTS_THEME` has the wrong shape, an unknown key or color name, or a color that is not `"#rrggbb"`             |
| `insights.W010` | `INSIGHTS_CHART_LIGHT_PRIMARY_COLOR` or `INSIGHTS_CHART_DARK_PRIMARY_COLOR` is still set; use `INSIGHTS_THEME`     |
| `insights.W011` | `INSIGHTS_DEFAULT_THEME` is not `light` or `dark`; `dark` is used                                                  |
| `insights.W012` | `INSIGHTS_CHART_DPI` is not a positive whole number; `180` is used                                                 |

To silence one, add it to `SILENCED_SYSTEM_CHECKS`:

```python
SILENCED_SYSTEM_CHECKS = ["insights.W003"]
```
