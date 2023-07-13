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
        'pdf/test/',
        views.InsightsPDFTestView.as_view(),
        name="insight_pdf_test",
    ),
    path(
        'pdf/',
        views.InsightsPDFView.as_view(),
        name="insight_pdf",
    ),
    path(
        'charts/<int:bucket_id>/',
        views.InsightsChartView.as_view(),
        name="insight_chart",
    ),
    path(
        '',
        views.InsightsDashboardView.as_view(),
        name="insight_dashboard",
    ),
]
