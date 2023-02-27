from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path(
        'insights/',
        include('django_insights.urls', namespace='insights'),
    ),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
