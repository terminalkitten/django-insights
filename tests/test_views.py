import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from django.urls import reverse

from django_insights.models import App, Bucket
from tests.utils import AllowAll, DenyAll, NoMethod

pytestmark = pytest.mark.django_db(databases=['default', 'insights'])


@pytest.mark.parametrize('name', ['insights:insight_dashboard', 'insights:insight_pdf'])
def test_pages_require_login(client, name):
    assert client.get(reverse(name)).status_code == 302


def test_chart_requires_login(client, bucket):
    response = client.get(reverse('insights:insight_chart', args=[bucket.pk]))
    assert response.status_code == 302


def test_dashboard_renders_counters(viewer_client, collected):
    response = viewer_client.get(reverse('insights:insight_dashboard'))
    assert response.status_code == 200
    assert 'How many books are there?' in response.content.decode()


def test_app_view_renders(viewer_client, collected):
    for app in App.objects.all():
        response = viewer_client.get(reverse('insights:insight_app', args=[app.pk]))
        assert response.status_code == 200


def test_every_bucket_renders_png(viewer_client, collected):
    assert Bucket.objects.exists()
    for bucket in Bucket.objects.all():
        response = viewer_client.get(
            reverse('insights:insight_chart', args=[bucket.pk])
        )
        assert response.status_code == 200
        assert response.content.startswith(b'\x89PNG')


def test_unknown_bucket_is_404(viewer_client):
    response = viewer_client.get(reverse('insights:insight_chart', args=[0]))
    assert response.status_code == 404


def test_unsupported_bucket_type_is_404(viewer_client):
    app = App.objects.create(module='tests.unsupported')
    unsupported = Bucket.objects.create(app=app, label='odd', type=99)
    response = viewer_client.get(
        reverse('insights:insight_chart', args=[unsupported.pk])
    )
    assert response.status_code == 404


def test_pdf_preview_renders_html(viewer_client, collected):
    response = viewer_client.get(reverse('insights:insight_pdf_test'))
    assert response.status_code == 200
    assert 'Insights' in response.content.decode()


@pytest.mark.parametrize(('permission', 'status'), [(AllowAll, 200), (DenyAll, 403)])
def test_dashboard_permissions(viewer_client, collected, permission, status):
    with override_settings(INSIGHT_DASHBOARD_PERMISSIONS=[permission]):
        response = viewer_client.get(reverse('insights:insight_dashboard'))
    assert response.status_code == status


def test_permission_without_has_permission_fails_closed(viewer_client, collected):
    with (
        override_settings(INSIGHT_DASHBOARD_PERMISSIONS=[AllowAll, NoMethod]),
        pytest.raises(ImproperlyConfigured, match='has_permission'),
    ):
        viewer_client.get(reverse('insights:insight_dashboard'))


def test_chart_permissions_are_enforced(viewer_client, bucket):
    with override_settings(INSIGHT_DASHBOARD_PERMISSIONS=[DenyAll]):
        response = viewer_client.get(
            reverse('insights:insight_chart', args=[bucket.pk])
        )
    assert response.status_code == 403


def test_chart_ignores_malicious_theme_cookie(viewer_client, bucket, tmp_path):
    viewer_client.cookies['theme'] = '../../evil'
    with override_settings(
        INSIGHT_CHARTS_USE_MEDIA_CACHE=True, INSIGHT_MEDIA_CACHE_ROOT=str(tmp_path)
    ):
        response = viewer_client.get(
            reverse('insights:insight_chart', args=[bucket.pk])
        )
    assert response.status_code == 200
    assert [path.name for path in tmp_path.rglob('*')] == [
        f'{bucket.type}-{bucket.pk}-dark.png'
    ]


def test_chart_cache_is_written_and_reused(viewer_client, bucket, tmp_path):
    url = reverse('insights:insight_chart', args=[bucket.pk])
    with override_settings(
        INSIGHT_CHARTS_USE_MEDIA_CACHE=True, INSIGHT_MEDIA_CACHE_ROOT=str(tmp_path)
    ):
        first = viewer_client.get(url)
        cached = tmp_path / f'{bucket.type}-{bucket.pk}-dark.png'
        assert cached.read_bytes() == first.content
        cached.write_bytes(b'cached')
        assert viewer_client.get(url).content == b'cached'


def test_chart_cache_without_root_fails_loudly(viewer_client, bucket):
    with (
        override_settings(
            INSIGHT_CHARTS_USE_MEDIA_CACHE=True, INSIGHT_MEDIA_CACHE_ROOT=None
        ),
        pytest.raises(ImproperlyConfigured, match='INSIGHT_MEDIA_CACHE_ROOT'),
    ):
        viewer_client.get(reverse('insights:insight_chart', args=[bucket.pk]))


def test_chart_survives_a_cache_file_removed_after_the_lookup(
    viewer_client, bucket, tmp_path, monkeypatch
):
    url = reverse('insights:insight_chart', args=[bucket.pk])
    with override_settings(
        INSIGHT_CHARTS_USE_MEDIA_CACHE=True, INSIGHT_MEDIA_CACHE_ROOT=str(tmp_path)
    ):
        viewer_client.get(url)
        (tmp_path / f'{bucket.type}-{bucket.pk}-dark.png').unlink()
        response = viewer_client.get(url)
    assert response.content.startswith(b'\x89PNG')
