from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from django.conf import settings as django_settings

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["settings"]

T = TypeVar("T")


class Setting(Generic[T]):
    """A Django setting with a default, read each time it is accessed"""

    def __init__(self, default: T) -> None:
        self.default = default
        self.name = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def __get__(self, instance: object, owner: type | None = None) -> T:
        return getattr(django_settings, self.name, self.default)


class InsightsSettings:
    INSIGHTS_APP_NAME: Setting[str] = Setting("MyApp")
    INSIGHTS_CHART_DPI: Setting[int] = Setting(180)
    INSIGHTS_DEFAULT_THEME: Setting[str] = Setting("dark")
    INSIGHTS_CHART_LIGHT_PRIMARY_COLOR: Setting[str] = Setting("#2563EB")
    INSIGHTS_CHART_DARK_PRIMARY_COLOR: Setting[str] = Setting("#BFDBFE")
    INSIGHTS_CHARTS_USE_MEDIA_CACHE: Setting[bool] = Setting(False)
    INSIGHTS_MEDIA_CACHE_ROOT: Setting[str | None] = Setting(None)
    INSIGHTS_DASHBOARD_PERMISSIONS: Setting[Sequence[type] | None] = Setting(None)


settings = InsightsSettings()
