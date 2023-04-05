from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = (
    [
        path(
            '',
            include('django_insights.urls', namespace='insights'),
        ),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
