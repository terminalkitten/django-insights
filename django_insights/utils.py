import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from django.core.exceptions import ImproperlyConfigured
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.signals import connection_created

from django_insights.settings import settings


class DjangoReadOnlyError(Exception):
    pass


def chart_cache_path(bucket_type: int, bucket_id: int, theme: str) -> Path | None:
    """Cache file of a rendered chart, None when the media cache is disabled"""
    if not settings.INSIGHT_CHARTS_USE_MEDIA_CACHE:
        return None

    root = settings.INSIGHT_MEDIA_CACHE_ROOT
    if not root:
        raise ImproperlyConfigured(
            'INSIGHT_MEDIA_CACHE_ROOT is required when INSIGHT_CHARTS_USE_MEDIA_CACHE is enabled'
        )
    return Path(root) / f'{bucket_type}-{bucket_id}-{theme}.png'


def write_atomic(path: Path, data: bytes) -> None:
    """Write through a temp file so readers never see a partial file"""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    try:
        with os.fdopen(handle, 'wb') as temp_file:
            temp_file.write(data)
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def rebuild_chart_media_cache() -> None:
    """Delete cached chart images, other files in the cache root are left alone"""
    if not (
        settings.INSIGHT_CHARTS_USE_MEDIA_CACHE and settings.INSIGHT_MEDIA_CACHE_ROOT
    ):
        return

    root = Path(settings.INSIGHT_MEDIA_CACHE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    for image in root.glob('*-*-*.png'):
        image.unlink()


def should_block(sql: str) -> bool:
    return not sql.lstrip(" \n(").startswith(
        (
            "EXPLAIN ",
            "PRAGMA ",
            "ROLLBACK TO SAVEPOINT ",
            "RELEASE SAVEPOINT ",
            "SAVEPOINT ",
            "SELECT ",
            "SET ",
        )
    ) and sql not in ("BEGIN", "COMMIT", "ROLLBACK")


def blocker(
    execute: Callable[[str, str, bool, dict[str, Any]], Any],
    sql: str,
    params: str,
    many: bool,
    context: dict[str, Any],
) -> Any:
    if should_block(sql):
        msg = "Write queries are currently disabled. Metrics MUST be read_only"
        raise DjangoReadOnlyError(msg)
    return execute(sql, params, many, context)


def install_hook(connection: BaseDatabaseWrapper, **kwargs: object) -> None:
    if blocker not in connection.execute_wrappers:  # pragma: no branch
        connection.execute_wrappers.insert(0, blocker)


class ReadOnly:
    def __init__(self, read_only_metric: Callable[..., Any]) -> None:
        self.read_only_metric = read_only_metric

    def __enter__(self) -> Callable[..., Any]:
        connection_created.connect(install_hook)
        return self.read_only_metric

    def __exit__(self, *args: object) -> None:
        connection_created.disconnect(install_hook)


read_only_mode = ReadOnly
