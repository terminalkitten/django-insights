from __future__ import annotations

from django.conf import settings as django_settings

__all__ = ["settings"]


class CustomSettings:
    """
    Django Insight settings

    """

    INSIGHTS_APP_NAME: str = "MyApp"
    INSIGHTS_CHART_DPI: int = 180
    INSIGHTS_DEFAULT_THEME = "dark"
    INSIGHTS_CHART_LIGHT_PRIMARY_COLOR = "#2563EB"
    INSIGHTS_CHART_DARK_PRIMARY_COLOR = "#BFDBFE"
    INSIGHT_CHARTS_USE_MEDIA_CACHE = False
    INSIGHT_MEDIA_CACHE_ROOT = None
    INSIGHT_DASHBOARD_PERMISSIONS = None

    def __getattribute__(self, name):
        try:
            return getattr(django_settings, name)
        except AttributeError:
            return super().__getattribute__(name)


settings = CustomSettings()
