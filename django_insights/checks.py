from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from django.apps.config import AppConfig
from django.conf import settings as django_settings
from django.core import checks
from django.core.checks import CheckMessage, register

from django_insights.database import database_entry
from django_insights.settings import settings

ROUTER = 'django_insights.database.Router'
RENAMED_SETTINGS = {
    'INSIGHT_CHARTS_USE_MEDIA_CACHE': 'INSIGHTS_CHARTS_USE_MEDIA_CACHE',
    'INSIGHT_MEDIA_CACHE_ROOT': 'INSIGHTS_MEDIA_CACHE_ROOT',
    'INSIGHT_DASHBOARD_PERMISSIONS': 'INSIGHTS_DASHBOARD_PERMISSIONS',
}


@register()
def check_database(
    app_configs: Sequence[AppConfig] | None, **kwargs: Any
) -> list[CheckMessage]:
    messages: list[CheckMessage] = []
    if database_entry not in django_settings.DATABASES:
        messages.append(
            checks.Warning(
                f"There is no '{database_entry}' entry in DATABASES.",
                hint="Add a SQLite database named 'insights' and run "
                "'migrate insights --database=insights'.",
                id='insights.W004',
            )
        )
    if ROUTER not in django_settings.DATABASE_ROUTERS:
        messages.append(
            checks.Warning(
                f'{ROUTER} is not in DATABASE_ROUTERS.',
                hint=f"Add '{ROUTER}' so insights are stored in the insights database.",
                id='insights.W005',
            )
        )
    return messages


@register()
def check_renamed_settings(
    app_configs: Sequence[AppConfig] | None, **kwargs: Any
) -> list[CheckMessage]:
    return [
        checks.Warning(
            f'{old} was renamed to {new}, the old name is ignored.',
            hint=f'Rename {old} to {new}.',
            id='insights.W006',
        )
        for old, new in RENAMED_SETTINGS.items()
        if hasattr(django_settings, old)
    ]


@register()
def check_media_cache(
    app_configs: Sequence[AppConfig] | None, **kwargs: Any
) -> list[CheckMessage]:
    if (
        settings.INSIGHTS_CHARTS_USE_MEDIA_CACHE
        and not settings.INSIGHTS_MEDIA_CACHE_ROOT
    ):
        return [
            checks.Warning(
                'INSIGHTS_MEDIA_CACHE_ROOT is required when '
                'INSIGHTS_CHARTS_USE_MEDIA_CACHE is enabled.',
                hint='Set INSIGHTS_MEDIA_CACHE_ROOT to a writable directory.',
                id='insights.W003',
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
            checks.Warning(
                'INSIGHTS_DASHBOARD_PERMISSIONS must be a list or tuple of classes.',
                id='insights.W001',
            )
        ]

    return [
        checks.Warning(
            f'{permission!r} in INSIGHTS_DASHBOARD_PERMISSIONS must be a class '
            'with a has_permission(request) method.',
            hint='The dashboard denies access until this is fixed.',
            id='insights.W002',
        )
        for permission in permissions
        if not (
            isinstance(permission, type)
            and callable(getattr(permission, 'has_permission', None))
        )
    ]
