from datetime import timedelta

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db import connections
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from django_insights import views
from django_insights.choices import BucketType
from django_insights.models import App, Bucket, BucketValue, Counter, Gauge
from tests.utils import AllowAll, DenyAll, NoMethod

pytestmark = pytest.mark.django_db(databases=['default', 'insights'])


@pytest.mark.parametrize('name', ['insights:insight_dashboard', 'insights:insight_pdf'])
def test_pages_require_login(client, name):
    assert client.get(reverse(name)).status_code == 302


def test_chart_requires_login(client, bucket):
    response = client.get(reverse('insights:insight_chart', args=[bucket.pk]))
    assert response.status_code == 302


def test_dashboard_renders_counters(collected, viewer_client):
    response = viewer_client.get(reverse('insights:insight_dashboard'))
    assert response.status_code == 200
    assert 'How many messages have been sent?' in response.content.decode()


def test_app_view_renders(collected, viewer_client):
    for app in App.objects.all():
        response = viewer_client.get(reverse('insights:insight_app', args=[app.pk]))
        assert response.status_code == 200


def test_every_bucket_renders_png(collected, viewer_client):
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


def test_pdf_preview_renders_html_in_debug(collected, viewer_client):
    with override_settings(DEBUG=True):
        response = viewer_client.get(reverse('insights:insight_pdf_test'))
    assert response.status_code == 200
    assert 'Insights' in response.content.decode()


def test_pdf_preview_is_hidden_outside_debug(collected, viewer_client):
    response = viewer_client.get(reverse('insights:insight_pdf_test'))
    assert response.status_code == 404


@pytest.mark.parametrize(('permission', 'status'), [(AllowAll, 200), (DenyAll, 403)])
def test_dashboard_permissions(collected, viewer_client, permission, status):
    with override_settings(INSIGHTS_DASHBOARD_PERMISSIONS=[permission]):
        response = viewer_client.get(reverse('insights:insight_dashboard'))
    assert response.status_code == status


def test_permission_without_has_permission_fails_closed(collected, viewer_client):
    with (
        override_settings(INSIGHTS_DASHBOARD_PERMISSIONS=[AllowAll, NoMethod]),
        pytest.raises(ImproperlyConfigured, match='has_permission'),
    ):
        viewer_client.get(reverse('insights:insight_dashboard'))


def test_chart_permissions_are_enforced(bucket, viewer_client):
    with override_settings(INSIGHTS_DASHBOARD_PERMISSIONS=[DenyAll]):
        response = viewer_client.get(
            reverse('insights:insight_chart', args=[bucket.pk])
        )
    assert response.status_code == 403


def test_chart_ignores_malicious_theme_cookie(bucket, viewer_client, tmp_path):
    viewer_client.cookies['theme'] = '../../evil'
    with override_settings(
        INSIGHTS_CHARTS_USE_MEDIA_CACHE=True, INSIGHTS_MEDIA_CACHE_ROOT=str(tmp_path)
    ):
        response = viewer_client.get(
            reverse('insights:insight_chart', args=[bucket.pk])
        )
    assert response.status_code == 200
    assert [path.name for path in tmp_path.rglob('*')] == [
        f'{bucket.type}-{bucket.pk}-dark.png'
    ]


def test_chart_cache_is_written_and_reused(bucket, viewer_client, tmp_path):
    url = reverse('insights:insight_chart', args=[bucket.pk])
    with override_settings(
        INSIGHTS_CHARTS_USE_MEDIA_CACHE=True, INSIGHTS_MEDIA_CACHE_ROOT=str(tmp_path)
    ):
        first = viewer_client.get(url)
        cached = tmp_path / f'{bucket.type}-{bucket.pk}-dark.png'
        assert cached.read_bytes() == first.content
        cached.write_bytes(b'cached')
        assert viewer_client.get(url).content == b'cached'


def test_chart_cache_without_root_fails_loudly(bucket, viewer_client):
    with (
        override_settings(
            INSIGHTS_CHARTS_USE_MEDIA_CACHE=True, INSIGHTS_MEDIA_CACHE_ROOT=None
        ),
        pytest.raises(ImproperlyConfigured, match='INSIGHTS_MEDIA_CACHE_ROOT'),
    ):
        viewer_client.get(reverse('insights:insight_chart', args=[bucket.pk]))


def test_chart_survives_a_cache_file_removed_after_the_lookup(
    bucket, viewer_client, tmp_path, monkeypatch
):
    url = reverse('insights:insight_chart', args=[bucket.pk])
    with override_settings(
        INSIGHTS_CHARTS_USE_MEDIA_CACHE=True, INSIGHTS_MEDIA_CACHE_ROOT=str(tmp_path)
    ):
        viewer_client.get(url)
        (tmp_path / f'{bucket.type}-{bucket.pk}-dark.png').unlink()
        response = viewer_client.get(url)
    assert response.content.startswith(b'\x89PNG')


def test_chart_is_private_and_has_a_validator(bucket, viewer_client):
    response = viewer_client.get(reverse('insights:insight_chart', args=[bucket.pk]))
    assert response['ETag']
    assert 'private' in response['Cache-Control']
    assert 'no-cache' in response['Cache-Control']


def test_unchanged_chart_is_not_rendered_again(bucket, viewer_client, monkeypatch):
    url = reverse('insights:insight_chart', args=[bucket.pk])
    etag = viewer_client.get(url)['ETag']

    def fail(*args, **kwargs):
        raise AssertionError('the chart was rendered again')

    monkeypatch.setattr(views, 'to_bytes_io', fail)
    response = viewer_client.get(url, HTTP_IF_NONE_MATCH=etag)

    assert response.status_code == 304
    assert response.content == b''


def test_chart_etag_depends_on_the_theme(bucket, viewer_client):
    url = reverse('insights:insight_chart', args=[bucket.pk])
    dark = viewer_client.get(url)['ETag']
    viewer_client.cookies['theme'] = 'light'
    assert viewer_client.get(url)['ETag'] != dark


def add_buckets(app, start, count):
    for number in range(start, start + count):
        for bucket_type in (
            BucketType.TIMESERIES,
            BucketType.SCATTERPLOT,
            BucketType.BARCHART,
            BucketType.HBARCHART,
        ):
            bucket = Bucket.objects.create(
                app=app, label=f'{bucket_type}-{number}', type=bucket_type
            )
            BucketValue.objects.bulk_create(
                BucketValue(bucket=bucket, xvalue=n, yvalue=n, category=str(n))
                for n in range(3)
            )


def app_page_queries(client, app):
    with CaptureQueriesContext(connections['insights']) as captured:
        response = client.get(reverse('insights:insight_app', args=[app.pk]))
    assert response.status_code == 200
    return len(captured)


def test_app_page_queries_do_not_grow_with_the_number_of_charts(viewer_client):
    app = App.objects.create(module='tests.many')
    add_buckets(app, start=0, count=1)
    few = app_page_queries(viewer_client, app)

    add_buckets(app, start=1, count=4)
    assert app_page_queries(viewer_client, app) == few


def get_html(client, url):
    response = client.get(url)
    assert response.status_code == 200
    return response.content.decode()


def test_sidebar_links_every_app_and_marks_the_current_one(collected, viewer_client):
    current = App.objects.get(label='Workspace')
    html = get_html(viewer_client, reverse('insights:insight_app', args=[current.pk]))

    for app in App.objects.all():
        assert reverse('insights:insight_app', args=[app.pk]) in html
    current_url = reverse('insights:insight_app', args=[current.pk])
    assert f'href="{current_url}" aria-current="page"' in html
    assert html.count('aria-current="page"') == 1


def test_the_dashboard_link_is_current_on_the_dashboard(collected, viewer_client):
    html = get_html(viewer_client, reverse('insights:insight_dashboard'))
    dashboard_url = reverse('insights:insight_dashboard')
    assert f'href="{dashboard_url}" aria-current="page"' in html
    assert html.count('aria-current="page"') == 1


@pytest.mark.parametrize(
    ('cookie', 'expected'),
    [(None, 'dark'), ('light', 'light'), ('dark', 'dark'), ('neon', 'dark')],
)
def test_the_page_theme_follows_the_cookie(viewer_client, cookie, expected):
    if cookie:
        viewer_client.cookies['theme'] = cookie
    html = get_html(viewer_client, reverse('insights:insight_dashboard'))
    assert f'<html lang="en" class="{expected}">' in html


def test_the_dashboard_explains_how_to_collect_when_it_is_empty(viewer_client):
    html = get_html(viewer_client, reverse('insights:insight_dashboard'))
    assert 'No insights yet' in html
    assert 'collect_insights' in html


def test_each_chart_has_one_image_and_a_data_dialog(collected, viewer_client):
    app = App.objects.get(label='Workspace')
    html = get_html(viewer_client, reverse('insights:insight_app', args=[app.pk]))

    buckets = Bucket.objects.filter(app=app)
    assert html.count('<img') == buckets.count()
    for bucket in buckets:
        assert f'id="bucket-data-{bucket.pk}"' in html
        assert f'id="insights-table-{bucket.pk}"' in html


def test_chart_texts_are_escaped(viewer_client):
    app = App.objects.create(module='tests.escape')
    Bucket.objects.create(
        app=app,
        label='x',
        type=BucketType.BARCHART,
        question='<script>alert(1)</script>',
        desc='<b>bold</b>',
    )
    html = get_html(viewer_client, reverse('insights:insight_app', args=[app.pk]))
    assert '<script>alert(1)</script>' not in html
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in html
    assert '<b>bold</b>' not in html


def test_the_top_bar_links_the_pdf_report_when_pymupdf_is_installed(viewer_client):
    html = get_html(viewer_client, reverse('insights:insight_dashboard'))
    assert f'href="{reverse("insights:insight_pdf")}"' in html


def test_the_top_bar_hides_the_pdf_report_without_pymupdf(viewer_client, monkeypatch):
    monkeypatch.setattr(views, 'pdf_available', lambda: False)
    html = get_html(viewer_client, reverse('insights:insight_dashboard'))
    assert reverse('insights:insight_pdf') not in html


def dashboard_queries(client):
    with CaptureQueriesContext(connections['insights']) as captured:
        response = client.get(reverse('insights:insight_dashboard'))
    assert response.status_code == 200
    return len(captured)


def add_stats(app, start, count):
    Counter.objects.bulk_create(
        Counter(app=app, label=f'c{n}', value=n, trend=[1.0, 2.0])
        for n in range(start, start + count)
    )
    Gauge.objects.bulk_create(
        Gauge(app=app, label=f'g{n}', value=n, trend=[2.0, 1.0])
        for n in range(start, start + count)
    )


def test_dashboard_queries_do_not_grow_with_the_number_of_stats(viewer_client):
    app = App.objects.create(module='tests.stats')
    add_stats(app, start=0, count=1)
    few = dashboard_queries(viewer_client)

    add_stats(app, start=1, count=5)
    assert dashboard_queries(viewer_client) == few


def test_last_collected_is_the_newest_moment_of_any_metric():
    app = App.objects.create(module='tests.moments')
    assert views.last_collected() is None

    old, new = timezone.now() - timedelta(days=2), timezone.now() - timedelta(days=1)
    Counter.objects.create(app=app, label='c', created_at=new)
    Gauge.objects.create(app=app, label='g', created_at=old)
    Bucket.objects.create(app=app, label='b', type=BucketType.BARCHART, created_at=old)

    assert views.last_collected() == new
