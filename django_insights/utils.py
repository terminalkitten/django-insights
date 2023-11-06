import os
import shutil
from typing import Any, Callable

from django.conf import settings
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.signals import connection_created


class DjangoReadOnlyError(Exception):
    pass


def rebuild_chart_media_cache() -> None:
    """
    Delete and recreate cache if cache is enabled and cache dir exists
    """
    if settings.INSIGHT_CHARTS_USE_MEDIA_CACHE and os.path.exists(
        settings.INSIGHT_MEDIA_CACHE_ROOT
    ):
        shutil.rmtree(settings.INSIGHT_MEDIA_CACHE_ROOT)
        os.mkdir(settings.INSIGHT_MEDIA_CACHE_ROOT)


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
    def __init__(self, read_only_metric):
        self.read_only_metric = read_only_metric

    def __enter__(self):
        connection_created.connect(install_hook)
        return self.read_only_metric

    def __exit__(*args, **kwargs):
        connection_created.disconnect(install_hook)


read_only_mode = ReadOnly
