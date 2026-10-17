# Settings

All settings are optional and read from your Django settings, every time they are used.

| Setting | Default | Description |
| --- | --- | --- |
| `INSIGHTS_APP_NAME` | `"MyApp"` | Name shown in the dashboard |
| `INSIGHTS_DEFAULT_THEME` | `"dark"` | `"light"` or `"dark"`, used until a visitor chooses a theme |
| `INSIGHTS_CHART_DPI` | `180` | Resolution of the chart images |
| `INSIGHTS_CHART_LIGHT_PRIMARY_COLOR` | `"#2563EB"` | Chart color in the light theme |
| `INSIGHTS_CHART_DARK_PRIMARY_COLOR` | `"#BFDBFE"` | Chart color in the dark theme |
| `INSIGHTS_CHARTS_USE_MEDIA_CACHE` | `False` | Keep rendered charts as files instead of rendering them on every request |
| `INSIGHTS_MEDIA_CACHE_ROOT` | `None` | Directory for the cached charts, required when the cache is on. Only cached chart images in it are deleted |
| `INSIGHTS_DASHBOARD_PERMISSIONS` | `None` | List of permission classes |

## Dashboard permissions

The dashboard always requires a logged in user. To restrict it further, add permission classes, every class must return `True`:

```python
class IsStaff:
    def has_permission(self, request):
        return request.user.is_staff


INSIGHTS_DASHBOARD_PERMISSIONS = [IsStaff]
```

A class without a `has_permission` method denies access, it never grants it.

## Checks

`python manage.py check` reports configuration problems as warnings, they never stop your project from starting:

| Id | Meaning |
| --- | --- |
| `insights.W001` | `INSIGHTS_DASHBOARD_PERMISSIONS` is not a list or tuple |
| `insights.W002` | an entry in `INSIGHTS_DASHBOARD_PERMISSIONS` is not a class with `has_permission` |
| `insights.W003` | the media cache is on, but `INSIGHTS_MEDIA_CACHE_ROOT` is not set |
| `insights.W004` | there is no `insights` entry in `DATABASES` |
| `insights.W005` | `django_insights.database.Router` is not in `DATABASE_ROUTERS` |
| `insights.W006` | a renamed setting is still set |

## Renamed settings

Version 2 renamed three settings to the `INSIGHTS_` prefix. The old names are ignored.

| Old | New |
| --- | --- |
| `INSIGHT_CHARTS_USE_MEDIA_CACHE` | `INSIGHTS_CHARTS_USE_MEDIA_CACHE` |
| `INSIGHT_MEDIA_CACHE_ROOT` | `INSIGHTS_MEDIA_CACHE_ROOT` |
| `INSIGHT_DASHBOARD_PERMISSIONS` | `INSIGHTS_DASHBOARD_PERMISSIONS` |
