from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from django.apps.config import AppConfig
from django.core.checks import CheckMessage, Error, register

from django_insights.settings import settings


@register()
def check_media_cache(
    app_configs: Sequence[AppConfig] | None, **kwargs: Any
) -> list[CheckMessage]:
    if (
        settings.INSIGHTS_CHARTS_USE_MEDIA_CACHE
        and not settings.INSIGHTS_MEDIA_CACHE_ROOT
    ):
        return [
            Error(
                'INSIGHTS_MEDIA_CACHE_ROOT is required when '
                'INSIGHTS_CHARTS_USE_MEDIA_CACHE is enabled.',
                id='insights.E003',
            )
        ]
    return []


@register()
def check_dashboard_permissions(
    app_configs: Sequence[AppConfig] | None, **kwargs: Any
) -> list[CheckMessage]:
    permissions = settings.INSIGHTS_DASHBOARD_PERMISSIONS
    if permissions is None:
        return []

    if not isinstance(permissions, list | tuple):
        return [
            Error(
                'INSIGHTS_DASHBOARD_PERMISSIONS must be a list or tuple of classes.',
                id='insights.E001',
            )
        ]

    return [
        Error(
            f'{permission!r} in INSIGHTS_DASHBOARD_PERMISSIONS must be a class '
            'with a has_permission(request) method.',
            id='insights.E002',
        )
        for permission in permissions
        if not (
            isinstance(permission, type)
            and callable(getattr(permission, 'has_permission', None))
        )
    ]
