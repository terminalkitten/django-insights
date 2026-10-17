import sys

import matplotlib
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


def test_rendering_charts_leaves_the_host_matplotlib_config_alone(collected):
    before = (
        list(matplotlib.rcParams['font.family']),
        list(matplotlib.rcParams['font.sans-serif']),
    )

    figure = charts.barchart(Bucket.objects.barcharts().earliest('pk'), theme='dark')
    to_bytes_io(figure)

    after = (
        list(matplotlib.rcParams['font.family']),
        list(matplotlib.rcParams['font.sans-serif']),
    )
    assert after == before


def test_figures_are_saved_with_the_bundled_font(collected, monkeypatch):
    figure = charts.barchart(Bucket.objects.barcharts().earliest('pk'), theme='dark')
    save = figure.savefig
    fonts = []

    def recording_save(*args, **kwargs):
        fonts.append(list(matplotlib.rcParams['font.sans-serif']))
        return save(*args, **kwargs)

    monkeypatch.setattr(figure, 'savefig', recording_save)
    to_bytes_io(figure)

    assert fonts == [['Ubuntu']]


def test_horizontal_bars_scale_to_small_values():
    app = App.objects.create(module='tests.small')
    bucket = Bucket.objects.create(app=app, label='bars', type=BucketType.HBARCHART)
    for xvalue, category in ((3, 'a'), (5, 'b')):
        BucketValue.objects.create(
            bucket=bucket, xvalue=xvalue, yvalue=xvalue, category=category
        )

    figure = charts.hbarchart(bucket, theme='dark')

    assert figure.axes[0].get_xlim()[1] < 10
