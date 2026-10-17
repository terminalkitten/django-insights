import os
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from django_insights.utils import (
    chart_cache_path,
    rebuild_chart_media_cache,
    write_atomic,
)


def test_rebuild_cache_only_deletes_cached_charts(tmp_path: Path):
    for name in ('1-3-dark.png', '2-4-light.png', 'keep.txt', 'logo.png'):
        (tmp_path / name).write_bytes(b'x')

    with override_settings(
        INSIGHTS_CHARTS_USE_MEDIA_CACHE=True, INSIGHTS_MEDIA_CACHE_ROOT=str(tmp_path)
    ):
        rebuild_chart_media_cache()

    assert sorted(path.name for path in tmp_path.iterdir()) == ['keep.txt', 'logo.png']


def test_rebuild_cache_creates_missing_root(tmp_path: Path):
    root = tmp_path / 'charts'
    with override_settings(
        INSIGHTS_CHARTS_USE_MEDIA_CACHE=True, INSIGHTS_MEDIA_CACHE_ROOT=str(root)
    ):
        rebuild_chart_media_cache()
    assert root.is_dir()


def test_rebuild_cache_does_nothing_when_disabled(tmp_path: Path):
    (tmp_path / '1-3-dark.png').write_bytes(b'x')
    with override_settings(
        INSIGHTS_CHARTS_USE_MEDIA_CACHE=False, INSIGHTS_MEDIA_CACHE_ROOT=str(tmp_path)
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
    with override_settings(INSIGHTS_CHARTS_USE_MEDIA_CACHE=False):
        assert chart_cache_path(1, 2, 'dark') is None


def test_chart_cache_path_requires_a_root():
    with (
        override_settings(
            INSIGHTS_CHARTS_USE_MEDIA_CACHE=True, INSIGHTS_MEDIA_CACHE_ROOT=None
        ),
        pytest.raises(ImproperlyConfigured, match='INSIGHTS_MEDIA_CACHE_ROOT'),
    ):
        chart_cache_path(1, 2, 'dark')


def test_chart_cache_path_is_inside_the_root(tmp_path: Path):
    with override_settings(
        INSIGHTS_CHARTS_USE_MEDIA_CACHE=True, INSIGHTS_MEDIA_CACHE_ROOT=str(tmp_path)
    ):
        assert chart_cache_path(3, 7, 'light') == tmp_path / '3-7-light.png'
