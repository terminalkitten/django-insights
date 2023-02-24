from django.urls import path

from django_insights import views

app_name = "insights"

urlpatterns = [
    path(
        'app/<uuid:app_uuid>/',
        views.InsightsAppView.as_view(),
        name="insight_app",
    ),
    path(
        '',
        views.InsightsDashboardView.as_view(),
        name="insight_dashboard",
    ),
]
