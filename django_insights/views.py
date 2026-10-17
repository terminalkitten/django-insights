from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models.query import QuerySet
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.generic import DetailView, ListView, View

from django_insights.charts import (
    barchart,
    hbarchart,
    scatterplot,
    timeseries,
    to_bytes_io,
)
from django_insights.models import App, Bucket, Counter, Gauge
from django_insights.pdf import html_to_pdf
from django_insights.settings import settings

THEMES = ('light', 'dark')


class CustomPermissionMixin(UserPassesTestMixin):
    """
    Run following permisssion

    class IsSomeAdminUser:
        def has_permission(self, request):
            return
    """

    def run_permissions(self, permissions: list[Callable]) -> list[bool]:
        """
        Run all permission checks from INSIGHT_DASHBOARD_PERMISSIONS settings
        and return output in array
        """
        return [
            permission().has_permission(request=self.request)
            for permission in permissions
            if hasattr(permission(), 'has_permission')
        ]

    def test_func(self):
        return (
            all(self.run_permissions(settings.INSIGHT_DASHBOARD_PERMISSIONS))
            if settings.INSIGHT_DASHBOARD_PERMISSIONS
            else True
        )


class InsightAppMixin(
    LoginRequiredMixin,
    CustomPermissionMixin,
    View,
):
    apps: QuerySet | list[App] = []

    def get_apps(self) -> QuerySet | list[App]:
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

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        app = self.get_object()

        context = super().get_context_data(**kwargs)
        context.update({'app_label': app.name})
        return context


class InsightsDashboardView(InsightAppMixin, ListView):
    template_name = "insights/dashboard.html"

    def get_queryset(self) -> list[Any]:
        # Get all metrics in one query?
        return Counter.objects.all()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({'gauges': Gauge.objects.all(), 'app_label': 'Dashboard'})
        return context


class InsightsChartView(LoginRequiredMixin, CustomPermissionMixin, View):
    def get(self, request, bucket_id):
        theme = self.request.COOKIES.get('theme')
        if theme not in THEMES:  # cookie is user input, it ends up in a file path
            theme = settings.INSIGHTS_DEFAULT_THEME
        bucket = get_object_or_404(Bucket, pk=bucket_id)

        filename: str = (
            f"{settings.INSIGHT_MEDIA_CACHE_ROOT}/{bucket.type}-{bucket.pk}-{theme}.png"
        )

        if os.path.exists(filename) and settings.INSIGHT_CHARTS_USE_MEDIA_CACHE:
            with open(filename, 'rb') as cached_image:
                buffer = cached_image.read()

            return HttpResponse(buffer, content_type='image/png')

        fig = None

        if bucket.is_timeseries:
            fig = timeseries(bucket, theme=theme)
        if bucket.is_scatterplot:
            fig = scatterplot(bucket, theme=theme)
        if bucket.is_barchart:
            fig = barchart(bucket, theme=theme)
        if bucket.is_hbarchart:
            fig = hbarchart(bucket, theme=theme)

        if fig is None:
            raise Http404("Unsupported bucket type")

        buffer = to_bytes_io(fig)

        if settings.INSIGHT_CHARTS_USE_MEDIA_CACHE:
            with open(filename, 'wb') as cached_image:
                cached_image.write(buffer)

        return HttpResponse(buffer, content_type='image/png')


class InsightsPDFView(InsightAppMixin, ListView):
    """Render PDF"""

    queryset = App.objects.all()
    template_name = 'insights/pdf.html'

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        html = render_to_string(
            self.template_name, self.get_context_data(), request=request
        )
        response = HttpResponse(html_to_pdf(html), content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="insights.pdf"'
        return response


class InsightsPDFTestView(InsightAppMixin, ListView):
    """Render PDF HTML as test"""

    queryset = App.objects.all()

    def get_template_names(self):
        return ['insights/pdf.html']

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        data = super().get_context_data(**kwargs)

        data.update(
            {
                'test_mode': True,
                'test_stylesheet': 'insights/css/pdf.css',
            }
        )

        return data
