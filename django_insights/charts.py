from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache, wraps
from pathlib import Path
from typing import TYPE_CHECKING, Any, ParamSpec

import matplotlib
import matplotlib.font_manager as fm
from matplotlib.figure import Figure

from django_insights import theme
from django_insights.choices import BucketType
from django_insights.models import Bucket, BucketValue
from django_insights.settings import settings

if TYPE_CHECKING:
    import datetime
    from collections.abc import Callable, Sequence
    from contextlib import AbstractContextManager

    from matplotlib.axes import Axes

FONT_FILE = Path(__file__).parent / 'static' / 'insights' / 'fonts' / 'ubuntu.ttf'
P = ParamSpec('P')


@lru_cache
def register_font() -> None:
    fm.fontManager.addfont(str(FONT_FILE))


def chart_style() -> AbstractContextManager[None]:
    register_font()
    return matplotlib.rc_context(
        {'font.family': 'sans-serif', 'font.sans-serif': ['Ubuntu']}
    )


def styled(func: Callable[P, Figure]) -> Callable[P, Figure]:
    """Apply the chart style only while the chart is built, never globally"""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Figure:
        with chart_style():
            return func(*args, **kwargs)

    return wrapper


class ChartSize(Enum):
    SMALL = 'small'
    MEDIUM = 'medium'
    LARGE = 'large'


@dataclass
class ThemeColor:
    primary: str
    face: str
    tick: str
    grid: str
    edge: str


def get_theme(name: str) -> ThemeColor:
    """Chart colors, from the same palette as the dashboard"""
    return ThemeColor(**theme.chart_colors(name))


FIGSIZES = {
    ChartSize.SMALL: (8, 4),
    ChartSize.MEDIUM: (16, 8),
    ChartSize.LARGE: (32, 16),
}


def get_figsize(size: ChartSize) -> tuple[int, int]:
    """Size of charts

    Args:
        size (ChartSize): SMALL, MEDIUM, LARGE

    Returns:
        tuple[int, int]: return tuple of figure size
    """

    return FIGSIZES[size]


LABEL_LENGTH = 30


def shorten(label: str) -> str:
    """Long category labels are cut so they do not push the bars away"""
    return label if len(label) <= LABEL_LENGTH else f'{label[: LABEL_LENGTH - 1]}…'


def bucket_rows(bucket: Bucket, *fields: str) -> list[tuple[Any, ...]]:
    """Plain rows in chart order, cheaper than loading a model per value"""
    return list(BucketValue.objects.filter(bucket=bucket).values_list(*fields))


def render_bucket(bucket: Bucket, theme: str) -> Figure:
    """The chart of a bucket, in the renderer of its type"""
    renderers = {
        BucketType.TIMESERIES: timeseries,
        BucketType.SCATTERPLOT: scatterplot,
        BucketType.BARCHART: barchart,
        BucketType.HBARCHART: hbarchart,
    }
    if bucket.type not in renderers:
        raise ValueError(f"Unsupported bucket type: {bucket.type}")
    return renderers[bucket.type](bucket, theme=theme)


def to_bytes_io(fig: Figure) -> bytes:
    """Render Matplotlib figure to file-like object"""
    flike = io.BytesIO()
    with chart_style():
        fig.savefig(flike, dpi=settings.INSIGHTS_CHART_DPI)

    return flike.getvalue()


def to_base64img(fig: Figure) -> str:
    """Render Matplotlib figure to Base64 encoded image"""
    return base64.b64encode(to_bytes_io(fig)).decode()


def prepare_plot(
    bucket: Bucket, theme: ThemeColor, size: ChartSize = ChartSize.SMALL
) -> tuple[Figure, Axes]:
    """Default plot options, used for all charts"""

    figsize = get_figsize(size)
    fig = Figure(figsize=figsize)
    ax = fig.subplots()
    fig.set_facecolor(theme.face)

    ax.tick_params(axis='x', colors=theme.tick)
    ax.tick_params(axis='y', colors=theme.tick)
    ax.set_facecolor(theme.face)
    ax.set_title(bucket.title)
    ax.set_ylabel(bucket.ylabel)
    ax.set_xlabel(bucket.xlabel)
    ax.yaxis.label.set_color(theme.tick)
    ax.xaxis.label.set_color(theme.tick)
    ax.grid(
        linestyle="dotted",
        linewidth=0.1,
        color=theme.grid,
        zorder=-10,
        visible=True,
    )

    for spine in ax.spines.values():
        spine.set_edgecolor(theme.edge)

    return fig, ax


def render_barchart(
    heights: Sequence[float],
    labels: Sequence[str],
    bucket: Bucket,
    theme: str,
    size: ChartSize,
) -> Figure:
    """Render barchart"""
    colors = get_theme(theme)
    fig, ax = prepare_plot(bucket, colors, size)
    ax.bar(labels, heights, color=colors.primary)

    return fig


def render_hbarchart(
    widths: Sequence[float],
    labels: Sequence[str],
    bucket: Bucket,
    theme: str,
    size: ChartSize,
) -> Figure:
    """Render horizontal barchart"""
    colors = get_theme(theme)
    fig, ax = prepare_plot(bucket, colors, size)
    bars = ax.barh(
        labels,
        widths,
        color=colors.primary,
        align='center',
        height=0.9,
    )

    for bar in bars:
        width = bar.get_width()
        label_y_pos = bar.get_y() + bar.get_height() / 2
        ax.text(
            width,
            label_y_pos,
            s=f'{width:,.0f}' if width == int(width) else f'{width:,.2f}',
            va='center',
            size=9,
            color=colors.tick,
        )

    for tick in ax.yaxis.get_major_ticks():
        tick.label1.set_fontsize(11)
        tick.label2.set_fontsize(11)

    ax.set_ylabel(bucket.xlabel)
    ax.set_xlabel(bucket.ylabel)

    _, xmax = ax.get_xlim()
    fig.subplots_adjust(left=0.3, right=0.9)
    ax.set_xlim(0, xmax * 1.1)
    return fig


def render_scatterplot(
    xaxis: Sequence[float],
    yaxis: Sequence[float],
    bucket: Bucket,
    theme: str,
    size: ChartSize,
) -> Figure:
    """Render scatterplot"""
    colors = get_theme(theme)

    fig, ax = prepare_plot(bucket, colors, size)
    ax.scatter(xaxis, yaxis, color=colors.primary)

    return fig


def render_timeseries(
    xaxis: Sequence[datetime.datetime],
    yaxis: Sequence[float],
    bucket: Bucket,
    theme: str,
    size: ChartSize,
) -> Figure:
    """Render timeseries"""
    colors = get_theme(theme)

    fig, ax = prepare_plot(bucket, colors, size)
    ax.plot(xaxis, yaxis, '--o', markersize=5, color=colors.primary)

    return fig


@styled
def barchart(bucket: Bucket, theme: str, size: ChartSize = ChartSize.SMALL) -> Figure:
    """Barchart"""
    rows = bucket_rows(bucket, 'xvalue', 'category')
    heights = [xvalue for xvalue, _ in rows]
    labels = [category or '' for _, category in rows]

    return render_barchart(heights, labels, bucket, theme, size)


@styled
def hbarchart(bucket: Bucket, theme: str, size: ChartSize = ChartSize.MEDIUM) -> Figure:
    """Horizontal Barchart"""
    rows = bucket_rows(bucket, 'xvalue', 'category')
    widths = [xvalue for xvalue, _ in rows]
    labels = [shorten(category or '') for _, category in rows]

    return render_hbarchart(widths, labels, bucket, theme, size)


@styled
def scatterplot(
    bucket: Bucket, theme: str, size: ChartSize = ChartSize.SMALL
) -> Figure:
    """Scatterplot chart"""
    rows = bucket_rows(bucket, 'xvalue', 'yvalue')
    xvalues = [xvalue for xvalue, _ in rows]
    yvalues = [yvalue for _, yvalue in rows]

    return render_scatterplot(yvalues, xvalues, bucket, theme, size)


@styled
def timeseries(bucket: Bucket, theme: str, size: ChartSize = ChartSize.SMALL) -> Figure:
    """Timeseries chart"""
    rows = bucket_rows(bucket, 'timestamp', 'xvalue')
    timestamps = [timestamp for timestamp, _ in rows]
    xvalues = [xvalue for _, xvalue in rows]

    return render_timeseries(timestamps, xvalues, bucket, theme, size)
