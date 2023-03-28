from __future__ import annotations

from django.conf import settings as django_settings

__all__ = ["settings"]


class CustomSettings:
    INSIGHTS_APP_NAME: str = "MyApp"
    INSIGHTS_MENU: dict[str, str] = {}
    INSIGHTS_CHART_DPI: int = 180

    INSIGHTS_CHART_LIGHT_PRIMARY_COLOR = "#2563EB"
    INSIGHTS_CHART_DARK_PRIMARY_COLOR = "#BFDBFE"

    INSIGHTS_DEFAULT_THEME = "dark"

    def __getattribute__(self, name):
        try:
            return getattr(django_settings, name)
        except AttributeError:
            return super().__getattribute__(name)


settings = CustomSettings()
