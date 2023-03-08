from __future__ import annotations

import base64
import io
import os
from dataclasses import dataclass

import matplotlib
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.ticker import LinearLocator

from django_insights.models import Bucket

matplotlib.use('Agg')
dir_path = os.path.dirname(os.path.realpath(__file__))
fm.fontManager.addfont(f"{dir_path}/static/insights/fonts/ubuntu.ttf")


plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = 'Ubuntu'


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
        primary="#3B82F6",
        face="#FEFEFE",
        tick="#333333",
        grid="#333333",
        edge="#FFFFFF",
    ),
    dark=ThemeColor(
        primary="#3B82F6",
        face="#0d1117",
        tick="#FEFEFE",
        grid="#FEFEFE",
        edge="#0d1117",
    ),
)


def to_base64img(fig) -> str:
    flike = io.BytesIO()
    fig.savefig(flike, dpi=130)
    return base64.b64encode(flike.getvalue()).decode()


def prepare_plot(bucket, theme):
    fig, ax = plt.subplots(figsize=(8, 4))
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
        linewidth=0.3,
        color=theme.grid,
        zorder=-10,
        visible=False,
    )

    for spine in ax.spines.values():
        spine.set_edgecolor(theme.edge)

    return fig, ax


def render_scatterplot(xaxis, yaxis, bucket, theme) -> str:
    theme = getattr(themes, theme)

    fig, ax = prepare_plot(bucket, theme)
    ax.scatter(xaxis, yaxis, color=theme.primary)
    return to_base64img(fig)


def render_timeseries(xaxis, yaxis, bucket, theme) -> str:
    theme = getattr(themes, theme)

    fig, ax = prepare_plot(bucket, theme)
    ax.plot(xaxis, yaxis, '--bo', markersize=5, color=theme.primary)

    # Date formatting
    fig.autofmt_xdate()
    ax.fmt_xdata = mdates.DateFormatter(bucket.xformat)
    ax.yaxis.set_minor_locator(LinearLocator(25))

    return to_base64img(fig)


def scatterplot(bucket: Bucket, theme: str) -> str:
    values = bucket.values.all()
    yvalues = [bucket_value.yvalue for bucket_value in values]
    xvalues = [bucket_value.xvalue for bucket_value in values]

    return render_scatterplot(yvalues, xvalues, bucket, theme)


def timeseries(bucket: Bucket, theme: str) -> str:
    values = bucket.values.all()

    yvalues = [bucket_value.timestamp for bucket_value in values]
    xvalues = [bucket_value.xvalue for bucket_value in values]

    return render_timeseries(yvalues, xvalues, bucket, theme)
