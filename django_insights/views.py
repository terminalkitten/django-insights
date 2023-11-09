from __future__ import annotations

import asyncio
import os
from typing import Any, Callable

from asgiref.sync import sync_to_async
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.utils.decorators import classonlymethod
from django.views.generic import DetailView, ListView, View
from django_weasyprint import WeasyTemplateResponseMixin

from django_insights.charts import (
    barchart,
    hbarchart,
    scatterplot,
    timeseries,
    to_bytes_io,
)
from django_insights.models import App, Bucket, Counter, Gauge
from django_insights.settings import settings


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


@sync_to_async
def get_bucket(bucket_id: int) -> Bucket:
    """Get bucket from async context"""
    return Bucket.objects.get(pk=bucket_id)


class InsightsChartView(LoginRequiredMixin, View):
    @classonlymethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        view._is_coroutine = asyncio.coroutines._is_coroutine
        return view

    async def get(self, request, bucket_id):
        theme = self.request.COOKIES.get('theme') or settings.INSIGHTS_DEFAULT_THEME
        bucket: Bucket = await get_bucket(bucket_id)

        filename: str = (
            f"{settings.INSIGHT_MEDIA_CACHE_ROOT}/{bucket.type}-{bucket.pk}-{theme}.png"
        )

        if os.path.exists(filename) and settings.INSIGHT_CHARTS_USE_MEDIA_CACHE:
            with open(filename, 'rb') as cached_image:
                buffer = cached_image.read()

            return HttpResponse(buffer, content_type='image/png')

        fig = None

        if bucket.is_timeseries:
            fig = await timeseries(bucket, theme=theme)
        if bucket.is_scatterplot:
            fig = await scatterplot(bucket, theme=theme)
        if bucket.is_barchart:
            fig = await barchart(bucket, theme=theme)
        if bucket.is_hbarchart:
            fig = await hbarchart(bucket, theme=theme)

        buffer = to_bytes_io(fig)

        if settings.INSIGHT_CHARTS_USE_MEDIA_CACHE:
            with open(filename, 'wb') as cached_image:
                cached_image.write(buffer)

        return HttpResponse(buffer, content_type='image/png')


class InsightsPDFView(WeasyTemplateResponseMixin, InsightAppMixin, ListView):
    """Render PDF"""

    queryset = App.objects.all()

    pdf_stylesheets = [
        settings.STATIC_ROOT + 'insights/css/pdf.css',
    ]

    template_name = 'insights/pdf.html'
    pdf_attachment = False
    pdf_filename = 'foo.pdf'


class InsightsPDFTestView(InsightAppMixin, ListView):
    """Render PDF HTML as test"""

    queryset = App.objects.all()

    pdf_stylesheets = [
        settings.STATIC_ROOT + 'insights/css/pdf.css',
    ]

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
