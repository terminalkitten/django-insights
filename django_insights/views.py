from __future__ import annotations

from typing import Any

from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.views.generic import DetailView, ListView, View

from django_insights.charts import barchart, scatterplot, timeseries, to_bytes_io
from django_insights.models import App, Bucket, Counter, Gauge
from django_insights.settings import settings


class InsightAppMixin(View):
    apps: list[App] = []

    def get_apps(self) -> QuerySet[App]:
        if not self.apps:
            self.apps = App.objects.all()
        return self.apps

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {'app_name': settings.INSIGHTS_APP_NAME, 'apps': self.get_apps()}
        )
        return context


class InsightsAppView(InsightAppMixin, DetailView):
    model = App
    slug_field = 'uuid'
    slug_url_kwarg = 'app_uuid'
    template_name = "insights/app.html"


class InsightsDashboardView(InsightAppMixin, ListView):
    template_name = "insights/dashboard.html"

    def get_queryset(self) -> list[Any]:
        return Counter.objects.all()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({'gauges': Gauge.objects.all()})
        return context


class InsightsChartView(View):
    def get(self, request, bucket_id):
        theme = self.request.COOKIES.get('theme')
        bucket = Bucket.objects.get(pk=bucket_id)

        fig = None

        if bucket.is_timeseries:
            fig = timeseries(bucket, theme=theme)
        if bucket.is_scatterplot:
            fig = scatterplot(bucket, theme=theme)
        if bucket.is_barchart:
            fig = barchart(bucket, theme=theme)

        buffer = to_bytes_io(fig)

        return HttpResponse(buffer, content_type='image/png')
