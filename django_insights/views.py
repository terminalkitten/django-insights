from __future__ import annotations

from typing import Any

import matplotlib

matplotlib.use('Agg')

import base64
import io
import os

import matplotlib.dates as mdates
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from django.db.models.query import QuerySet
from django.views.generic import DetailView, ListView, View
from matplotlib.ticker import LinearLocator

from django_insights.models import App, Counter, Gauge

dir_path = os.path.dirname(os.path.realpath(__file__))
fm.fontManager.addfont(f"{dir_path}/static/insights/fonts/montserrat.ttf")


plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = 'Montserrat'


def to_base64img(fig) -> str:
    flike = io.BytesIO()
    fig.savefig(flike, dpi=130)
    return base64.b64encode(flike.getvalue()).decode()


def prepare_plot(bucket):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.tick_params(axis='x', colors='#333')
    ax.tick_params(axis='y', colors='#333')
    ax.set_facecolor("#FEFEFE")
    ax.set_title(bucket.title)
    ax.set_ylabel(bucket.ylabel)
    ax.set_xlabel(bucket.xlabel)
    ax.grid(
        linestyle="dotted",
        linewidth=0.3,
        color='#333',
        zorder=-10,
        visible=False,
    )

    for spine in ax.spines.values():
        spine.set_edgecolor('#fff')

    return fig, ax


def render_scatterplot(xaxis, yaxis, bucket) -> str:
    fig, ax = prepare_plot(bucket)
    ax.scatter(xaxis, yaxis)
    return to_base64img(fig)


def render_timeseries(xaxis, yaxis, bucket) -> str:
    fig, ax = prepare_plot(bucket)
    ax.plot(xaxis, yaxis, '--bo', markersize=5, color='#3B82F6')

    # Date formatting
    fig.autofmt_xdate()
    ax.fmt_xdata = mdates.DateFormatter(bucket.xformat)
    ax.yaxis.set_minor_locator(LinearLocator(25))

    return to_base64img(fig)


class InsightAppMenuMixin(View):
    apps: list[App] = []

    def get_apps(self) -> QuerySet[App]:
        if not self.apps:
            self.apps = App.objects.all()
        return self.apps

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({'apps': self.get_apps()})
        return context


class InsightsAppView(InsightAppMenuMixin, DetailView):
    model = App
    slug_field = 'uuid'
    slug_url_kwarg = 'app_uuid'
    template_name = "insights/app.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        app = self.get_object()

        timeseries_charts = []
        scatterplot_charts = []

        for bucket in app.buckets.timeseries():
            values = bucket.values.all()
            if not values:
                timeseries_charts.append((bucket, None, values))
                continue

            yvalues = [bucket_value.timestamp for bucket_value in values]
            xvalues = [bucket_value.xvalue for bucket_value in values]

            chart = render_timeseries(yvalues, xvalues, bucket)
            timeseries_charts.append((bucket, chart, values))

        for bucket in app.buckets.scatterplots():
            values = bucket.values.all()

            if not values:
                scatterplot_charts.append((bucket, None, values))
                continue

            yvalues = [bucket_value.yvalue for bucket_value in values]
            xvalues = [bucket_value.xvalue for bucket_value in values]

            chart = render_scatterplot(yvalues, xvalues, bucket)
            scatterplot_charts.append((bucket, chart, values))

        context['timeseries'] = timeseries_charts
        context['scatterplots'] = scatterplot_charts

        return context


class InsightsDashboardView(InsightAppMenuMixin, ListView):
    template_name = "insights/dashboard.html"

    def get_queryset(self) -> list[Any]:
        return Counter.objects.all()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({'gauges': Gauge.objects.all()})
        return context
