import os
import tempfile
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from django_insights.settings import settings


def chart_cache_path(bucket_type: int, bucket_id: int, mode: str) -> Path | None:
    """Cache file of a rendered chart, None when the media cache is disabled"""
    if not settings.INSIGHTS_CHARTS_USE_MEDIA_CACHE:
        return None

    root = settings.INSIGHTS_MEDIA_CACHE_ROOT
    if not root:
        raise ImproperlyConfigured(
            'INSIGHTS_MEDIA_CACHE_ROOT is required when INSIGHTS_CHARTS_USE_MEDIA_CACHE is enabled'
        )
    return Path(root) / f'{bucket_type}-{bucket_id}-{mode}.png'


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
        settings.INSIGHTS_CHARTS_USE_MEDIA_CACHE and settings.INSIGHTS_MEDIA_CACHE_ROOT
    ):
        return

    root = Path(settings.INSIGHTS_MEDIA_CACHE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    for image in root.glob('*-*-*.png'):
        image.unlink()
