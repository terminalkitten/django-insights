import sys

import pytest
from matplotlib.figure import Figure

from django_insights import charts
from django_insights.charts import to_base64img, to_bytes_io
from django_insights.choices import BucketType
from django_insights.models import App, Bucket, BucketValue

pytestmark = pytest.mark.django_db(databases=['default', 'insights'])


@pytest.mark.parametrize('theme', ['light', 'dark'])
def test_every_bucket_renders_in_both_themes(collected, theme):
    renderers = {
        Bucket.objects.timeseries: charts.timeseries,
        Bucket.objects.scatterplots: charts.scatterplot,
        Bucket.objects.barcharts: charts.barchart,
        Bucket.objects.hbarcharts: charts.hbarchart,
    }
    for queryset, render in renderers.items():
        figure = render(queryset().earliest('pk'), theme=theme)
        assert isinstance(figure, Figure)
        assert to_bytes_io(figure).startswith(b'\x89PNG')


def test_base64_image_is_png(collected):
    figure = charts.barchart(Bucket.objects.barcharts().earliest('pk'), theme='light')
    assert to_base64img(figure).startswith('iVBOR')


def test_charts_do_not_use_pyplot(collected):
    charts.timeseries(Bucket.objects.timeseries().earliest('pk'), theme='dark')
    assert 'matplotlib.pyplot' not in sys.modules


@pytest.mark.parametrize(
    ('render', 'bucket_type'),
    [(charts.barchart, BucketType.BARCHART), (charts.hbarchart, BucketType.HBARCHART)],
)
def test_bars_without_a_category_still_render(render, bucket_type):
    app = App.objects.create(module='tests.uncategorized')
    bucket = Bucket.objects.create(app=app, label='bars', type=bucket_type)
    BucketValue.objects.create(bucket=bucket, xvalue=3, yvalue=1, category=None)
    BucketValue.objects.create(bucket=bucket, xvalue=5, yvalue=2, category='north')

    assert to_bytes_io(render(bucket, theme='dark')).startswith(b'\x89PNG')


def test_unknown_theme_is_rejected():
    with pytest.raises(ValueError, match='Unknown theme'):
        charts.get_theme('neon')
