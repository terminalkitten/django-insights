import os
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test import override_settings

from django_insights.utils import (
    DjangoReadOnlyError,
    blocker,
    chart_cache_path,
    install_hook,
    rebuild_chart_media_cache,
    should_block,
    write_atomic,
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


def test_write_atomic_creates_directories_and_leaves_no_temp_files(tmp_path: Path):
    target = tmp_path / 'nested' / 'chart.png'
    write_atomic(target, b'png')
    assert target.read_bytes() == b'png'
    assert [path.name for path in target.parent.iterdir()] == ['chart.png']


def test_write_atomic_keeps_previous_file_when_replace_fails(
    tmp_path: Path, monkeypatch
):
    target = tmp_path / 'chart.png'
    target.write_bytes(b'old')

    def fail(*args):
        raise OSError('disk full')

    monkeypatch.setattr(os, 'replace', fail)
    with pytest.raises(OSError, match='disk full'):
        write_atomic(target, b'new')

    assert target.read_bytes() == b'old'
    assert [path.name for path in tmp_path.iterdir()] == ['chart.png']


def test_chart_cache_path_is_none_when_disabled():
    with override_settings(INSIGHT_CHARTS_USE_MEDIA_CACHE=False):
        assert chart_cache_path(1, 2, 'dark') is None


def test_chart_cache_path_requires_a_root():
    with (
        override_settings(
            INSIGHT_CHARTS_USE_MEDIA_CACHE=True, INSIGHT_MEDIA_CACHE_ROOT=None
        ),
        pytest.raises(ImproperlyConfigured, match='INSIGHT_MEDIA_CACHE_ROOT'),
    ):
        chart_cache_path(1, 2, 'dark')


def test_chart_cache_path_is_inside_the_root(tmp_path: Path):
    with override_settings(
        INSIGHT_CHARTS_USE_MEDIA_CACHE=True, INSIGHT_MEDIA_CACHE_ROOT=str(tmp_path)
    ):
        assert chart_cache_path(3, 7, 'light') == tmp_path / '3-7-light.png'
