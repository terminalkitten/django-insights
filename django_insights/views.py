from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

from django.conf import settings as django_settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.cache import patch_cache_control
from django.utils.decorators import method_decorator
from django.views.decorators.http import condition
from django.views.generic import DetailView, ListView, View
from django.views.generic.base import ContextMixin

from django_insights import theme
from django_insights.charts import render_bucket, to_bytes_io
from django_insights.models import App, Bucket, Counter, Gauge
from django_insights.pdf import html_to_pdf, pdf_available
from django_insights.settings import settings
from django_insights.utils import chart_cache_path, write_atomic

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import datetime

    from django.db.models.query import QuerySet

THEMES = ('light', 'dark')


def chart_theme(request: HttpRequest) -> str:
    theme = request.COOKIES.get('theme')
    return theme if theme in THEMES else settings.INSIGHTS_DEFAULT_THEME


def chart_etag(request: HttpRequest, bucket_id: int) -> str | None:
    """Identifies one rendered chart, a collect creates new buckets so it never changes"""
    created_at = (
        Bucket.objects.filter(pk=bucket_id).values_list('created_at', flat=True).first()
    )
    if created_at is None:
        return None

    key = '|'.join(
        str(part)
        for part in (
            bucket_id,
            created_at.isoformat(),
            chart_theme(request),
            settings.INSIGHTS_CHART_DPI,
            theme.fingerprint(),
        )
    )
    return hashlib.sha256(key.encode()).hexdigest()


def png_response(content: bytes) -> HttpResponse:
    response = HttpResponse(content, content_type='image/png')
    patch_cache_control(response, private=True, no_cache=True)
    return response


class CustomPermissionMixin(UserPassesTestMixin):
    """Deny access unless every INSIGHTS_DASHBOARD_PERMISSIONS class grants it"""

    request: HttpRequest

    def run_permissions(self, permissions: Iterable[type]) -> list[bool]:
        """Run has_permission(request) of every configured permission class"""
        results = []
        for permission_class in permissions:
            has_permission = getattr(permission_class(), 'has_permission', None)
            if not callable(has_permission):
                raise ImproperlyConfigured(
                    f'{permission_class!r} in INSIGHTS_DASHBOARD_PERMISSIONS '
                    'has no has_permission(request) method'
                )
            results.append(bool(has_permission(request=self.request)))
        return results

    def test_func(self) -> bool:
        permissions = settings.INSIGHTS_DASHBOARD_PERMISSIONS or []
        return all(self.run_permissions(permissions))


def last_collected() -> datetime | None:
    """When the insights were collected last, None before the first collect"""
    newest = (
        Counter.objects.order_by()
        .values_list('created_at')
        .union(
            Gauge.objects.order_by().values_list('created_at'),
            Bucket.objects.order_by().values_list('created_at'),
        )
        .order_by('-created_at')[:1]
    )
    return next(iter(newest), (None,))[0]


class InsightAppMixin(
    LoginRequiredMixin,
    CustomPermissionMixin,
    ContextMixin,
    View,
):
    apps: QuerySet | list[App] | None = None

    def get_apps(self) -> QuerySet | list[App]:
        if self.apps is None:
            self.apps = App.objects.all()
        return self.apps

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'app_name': settings.INSIGHTS_APP_NAME,
                'apps': self.get_apps(),
                'theme': chart_theme(self.request),
                'current_app': None,
                'pdf_available': pdf_available(),
                'last_collected': last_collected(),
                'stylesheet': theme.stylesheet(),
                'theme_css': theme.css_overrides(),
            }
        )
        return context


class InsightsAppView(InsightAppMixin, DetailView):
    model = App
    slug_field = 'uuid'
    slug_url_kwarg = 'app_uuid'
    template_name = "insights/app.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'app_label': self.object.name,
                'current_app': self.object,
                'buckets': Bucket.objects.filter(app=self.object).prefetch_related(
                    'values'
                ),
            }
        )
        return context


class InsightsDashboardView(InsightAppMixin, ListView):
    template_name = "insights/dashboard.html"

    def get_queryset(self) -> QuerySet[Counter]:
        return Counter.objects.select_related('app')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {'gauges': Gauge.objects.select_related('app'), 'app_label': 'Dashboard'}
        )
        return context


class InsightsChartView(LoginRequiredMixin, CustomPermissionMixin, View):
    @method_decorator(condition(etag_func=chart_etag))
    def get(self, request: HttpRequest, bucket_id: int) -> HttpResponse:
        theme = chart_theme(request)
        bucket = get_object_or_404(Bucket, pk=bucket_id)

        cache_path = chart_cache_path(bucket.type, bucket.pk, theme)
        if cache_path is not None:
            try:
                return png_response(cache_path.read_bytes())
            except FileNotFoundError:
                pass

        try:
            buffer = to_bytes_io(render_bucket(bucket, theme))
        except ValueError as error:
            raise Http404(str(error)) from error

        if cache_path is not None:
            write_atomic(cache_path, buffer)

        return png_response(buffer)


class InsightsPDFView(InsightAppMixin, ListView):
    """Render PDF"""

    queryset = App.objects.all()
    template_name = 'insights/pdf.html'

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object_list = self.get_queryset()
        html = render_to_string(
            self.get_template_names(), self.get_context_data(), request=request
        )
        response = HttpResponse(html_to_pdf(html), content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="insights.pdf"'
        return response


class InsightsPDFTestView(InsightAppMixin, ListView):
    """Render PDF HTML as test, only available when DEBUG is on"""

    queryset = App.objects.all()

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not django_settings.DEBUG:
            raise Http404("The PDF preview is only available when DEBUG is on")
        return super().get(request, *args, **kwargs)

    def get_template_names(self) -> list[str]:
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
