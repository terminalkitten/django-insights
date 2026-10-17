from pathlib import Path

import pytest
from django.db import connection
from django.test import override_settings

from django_insights.utils import (
    DjangoReadOnlyError,
    blocker,
    install_hook,
    rebuild_chart_media_cache,
    should_block,
)


@pytest.mark.parametrize(
    'sql',
    [
        'SELECT 1',
        '  (SELECT 1)',
        'EXPLAIN SELECT 1',
        'PRAGMA table_info(x)',
        'SAVEPOINT s1',
        'RELEASE SAVEPOINT s1',
        'ROLLBACK TO SAVEPOINT s1',
        'SET x = 1',
        'BEGIN',
        'COMMIT',
        'ROLLBACK',
    ],
)
def test_read_statements_are_allowed(sql):
    assert should_block(sql) is False


@pytest.mark.parametrize(
    'sql',
    [
        'INSERT INTO t VALUES (1)',
        'UPDATE t SET a = 1',
        'DELETE FROM t',
        'DROP TABLE t',
        'CREATE TABLE t (a int)',
    ],
)
def test_write_statements_are_blocked(sql):
    assert should_block(sql) is True


def test_blocker_raises_for_writes():
    with pytest.raises(DjangoReadOnlyError, match='read_only'):
        blocker(lambda *args: None, 'DELETE FROM t', '', False, {})


def test_blocker_passes_reads_through():
    assert blocker(lambda *args: 'rows', 'SELECT 1', '', False, {}) == 'rows'


def test_install_hook_is_idempotent():
    connection.execute_wrappers.clear()
    try:
        install_hook(connection)
        install_hook(connection)
        assert connection.execute_wrappers.count(blocker) == 1
    finally:
        connection.execute_wrappers.clear()


def test_rebuild_cache_only_deletes_cached_charts(tmp_path: Path):
    for name in ('1-3-dark.png', '2-4-light.png', 'keep.txt', 'logo.png'):
        (tmp_path / name).write_bytes(b'x')

    with override_settings(
        INSIGHT_CHARTS_USE_MEDIA_CACHE=True, INSIGHT_MEDIA_CACHE_ROOT=str(tmp_path)
    ):
        rebuild_chart_media_cache()

    assert sorted(path.name for path in tmp_path.iterdir()) == ['keep.txt', 'logo.png']


def test_rebuild_cache_creates_missing_root(tmp_path: Path):
    root = tmp_path / 'charts'
    with override_settings(
        INSIGHT_CHARTS_USE_MEDIA_CACHE=True, INSIGHT_MEDIA_CACHE_ROOT=str(root)
    ):
        rebuild_chart_media_cache()
    assert root.is_dir()


def test_rebuild_cache_does_nothing_when_disabled(tmp_path: Path):
    (tmp_path / '1-3-dark.png').write_bytes(b'x')
    with override_settings(
        INSIGHT_CHARTS_USE_MEDIA_CACHE=False, INSIGHT_MEDIA_CACHE_ROOT=str(tmp_path)
    ):
        rebuild_chart_media_cache()
    assert (tmp_path / '1-3-dark.png').exists()
