from __future__ import annotations

import base64
import io
import os
from dataclasses import dataclass
from enum import Enum

import matplotlib
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
from matplotlib.figure import Figure

from django_insights.models import Bucket
from django_insights.settings import settings

dir_path = os.path.dirname(os.path.realpath(__file__))
fm.fontManager.addfont(f"{dir_path}/static/insights/fonts/ubuntu.ttf")


matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = 'Ubuntu'


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


@dataclass
class Theme:
    dark: ThemeColor
    light: ThemeColor


themes = Theme(
    light=ThemeColor(
        primary=settings.INSIGHTS_CHART_LIGHT_PRIMARY_COLOR,
        face="#FEFEFE",
        tick="#333333",
        grid="#333333",
        edge="#FFFFFF",
    ),
    dark=ThemeColor(
        primary=settings.INSIGHTS_CHART_DARK_PRIMARY_COLOR,
        face="#0d1117",
        tick="#FEFEFE",
        grid="#FEFEFE",
        edge="#0d1117",
    ),
)


def get_figsize(size: ChartSize) -> tuple[int, int]:
    """Size of charts

    Args:
        size (ChartSize): SMALL, MEDIUM, LARGE

    Returns:
        tuple[int, int]: return tuple of figure siza
    """

    if size == ChartSize.SMALL:
        return (8, 4)
    if size == ChartSize.MEDIUM:
        return (16, 8)
    if size == ChartSize.LARGE:
        return (32, 16)


def to_bytes_io(fig) -> bytes:
    """Render Mathplotlib figure to file-like object"""
    flike = io.BytesIO()
    fig.savefig(flike, dpi=settings.INSIGHTS_CHART_DPI)

    return flike.getvalue()


def to_base64img(fig) -> str:
    """Render Mathplotlib figure to Base64 encoded image"""
    return base64.b64encode(to_bytes_io(fig)).decode()


def prepare_plot(bucket, theme, size: ChartSize = ChartSize.SMALL):
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


def render_barchart(yaxis, xaxis, labels, bucket, theme, size) -> str:
    """Render barchart"""
    theme = getattr(themes, theme)
    fig, ax = prepare_plot(bucket, theme, size)
    ax.bar(labels, xaxis, color=theme.primary)

    return fig


def render_hbarchart(yaxis, xaxis, labels, combined_labels, bucket, theme, size) -> str:
    """Render horizontal barchart"""
    theme = getattr(themes, theme)
    fig, ax = prepare_plot(bucket, theme, size)
    bars = ax.barh(
        combined_labels,
        xaxis,
        color=theme.primary,
        align='center',
        height=0.9,
    )

    for bar in bars:
        width = bar.get_width()
        label_y_pos = bar.get_y() + bar.get_height() / 2
        ax.text(width, label_y_pos, s=f'{width}', va='center', size=4)

    for tick in ax.yaxis.get_major_ticks():
        tick.label1.set_fontsize(6)
        tick.label2.set_fontsize(6)

    ax.set_ylabel(bucket.xlabel)
    ax.set_xlabel(bucket.ylabel)

    _, xmax = ax.get_xlim()
    fig.subplots_adjust(left=0.3, right=0.9)
    ax.set_xlim(0, xmax + 100)
    return fig


def render_scatterplot(xaxis, yaxis, bucket, theme, size) -> str:
    """Render scatterplot"""
    theme = getattr(themes, theme)

    fig, ax = prepare_plot(bucket, theme, size)
    ax.scatter(xaxis, yaxis, color=theme.primary)

    return fig


def render_timeseries(xaxis, yaxis, bucket, theme, size) -> str:
    """Render timeseries"""
    theme = getattr(themes, theme)

    fig, ax = prepare_plot(bucket, theme, size)
    ax.plot(xaxis, yaxis, '--o', markersize=5, color=theme.primary)

    # Date formatting
    ax.fmt_xdata = mdates.DateFormatter(bucket.xformat)

    return fig


def barchart(bucket: Bucket, theme: str, size: ChartSize = ChartSize.SMALL) -> str:
    """Barchart"""
    values = bucket.values.all()
    yvalues = [bucket_value.yvalue for bucket_value in values]
    xvalues = [bucket_value.xvalue for bucket_value in values]
    labels = [bucket_value.category for bucket_value in values]

    return render_barchart(yvalues, xvalues, labels, bucket, theme, size)


def hbarchart(bucket: Bucket, theme: str, size: ChartSize = ChartSize.MEDIUM) -> str:
    """Horizontal Barchart"""
    values = bucket.values.all()
    yvalues = [bucket_value.yvalue for bucket_value in values]
    xvalues = [bucket_value.xvalue for bucket_value in values]
    labels = [bucket_value.category for bucket_value in values]

    combined_labels = [
        f"{bucket_value.category[0:30]}..:{int(bucket_value.yvalue)}"
        for bucket_value in values
    ]

    return render_hbarchart(
        yvalues, xvalues, labels, combined_labels, bucket, theme, size
    )


def scatterplot(bucket: Bucket, theme: str, size: ChartSize = ChartSize.SMALL) -> str:
    """Scatterplot chart"""
    values = bucket.values.all()
    yvalues = [bucket_value.yvalue for bucket_value in values]
    xvalues = [bucket_value.xvalue for bucket_value in values]

    return render_scatterplot(yvalues, xvalues, bucket, theme, size)


def timeseries(bucket: Bucket, theme: str, size: ChartSize = ChartSize.SMALL) -> str:
    """Timeseries chart"""
    values = bucket.values.all()

    yvalues = [bucket_value.timestamp for bucket_value in values]
    xvalues = [bucket_value.xvalue for bucket_value in values]

    return render_timeseries(yvalues, xvalues, bucket, theme, size)
