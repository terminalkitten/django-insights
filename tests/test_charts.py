import io
import sys

import matplotlib
import matplotlib.image
import pytest
from django.test import override_settings
from matplotlib.figure import Figure

from django_insights import charts, theme
from django_insights.charts import to_bytes_io
from django_insights.choices import BucketType
from django_insights.models import App, Bucket, BucketValue
from django_insights.settings import DEFAULT_DPI

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
        figure = render(queryset().earliest('pk'), mode=theme)
        assert isinstance(figure, Figure)
        assert to_bytes_io(figure).startswith(b'\x89PNG')


def test_charts_do_not_use_pyplot(collected):
    charts.timeseries(Bucket.objects.timeseries().earliest('pk'), mode='dark')
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

    assert to_bytes_io(render(bucket, mode='dark')).startswith(b'\x89PNG')


def test_unknown_theme_is_rejected():
    with pytest.raises(ValueError, match='Unknown theme'):
        theme.chart_colors('neon')


def test_rendering_charts_leaves_the_host_matplotlib_config_alone(collected):
    before = (
        list(matplotlib.rcParams['font.family']),
        list(matplotlib.rcParams['font.sans-serif']),
    )

    figure = charts.barchart(Bucket.objects.barcharts().earliest('pk'), mode='dark')
    to_bytes_io(figure)

    after = (
        list(matplotlib.rcParams['font.family']),
        list(matplotlib.rcParams['font.sans-serif']),
    )
    assert after == before


def test_figures_are_saved_with_the_bundled_font(collected, monkeypatch):
    figure = charts.barchart(Bucket.objects.barcharts().earliest('pk'), mode='dark')
    save = figure.savefig
    fonts = []

    def recording_save(*args, **kwargs):
        fonts.append(list(matplotlib.rcParams['font.sans-serif']))
        return save(*args, **kwargs)

    monkeypatch.setattr(figure, 'savefig', recording_save)
    to_bytes_io(figure)

    assert fonts == [['Geist']]


def test_horizontal_bars_scale_to_small_values():
    app = App.objects.create(module='tests.small')
    bucket = Bucket.objects.create(app=app, label='bars', type=BucketType.HBARCHART)
    for xvalue, category in ((3, 'a'), (5, 'b')):
        BucketValue.objects.create(
            bucket=bucket, xvalue=xvalue, yvalue=xvalue, category=category
        )

    figure = charts.hbarchart(bucket, mode='dark')

    assert figure.axes[0].get_xlim()[1] < 10


def test_horizontal_bar_labels_are_readable_on_the_theme():
    app = App.objects.create(module='tests.labels')
    bucket = Bucket.objects.create(app=app, label='bars', type=BucketType.HBARCHART)
    BucketValue.objects.create(bucket=bucket, xvalue=1200, yvalue=0, category='a')

    figure = charts.hbarchart(bucket, mode='dark')

    (text,) = figure.axes[0].texts
    assert text.get_text() == '1,200'
    assert text.get_color() == theme.chart_colors('dark')['tick']


def test_only_long_category_labels_are_shortened():
    assert charts.shorten('short') == 'short'
    assert charts.shorten('x' * 31) == 'x' * 29 + '…'


@pytest.mark.parametrize(
    ('render', 'bucket_type'),
    [(charts.barchart, BucketType.BARCHART), (charts.hbarchart, BucketType.HBARCHART)],
)
def test_long_labels_stay_inside_the_image(render, bucket_type):
    app = App.objects.create(module='tests.long')
    bucket = Bucket.objects.create(
        app=app, label='bars', type=bucket_type, xlabel='Workspace name', ylabel='Total'
    )
    for number in range(6):
        BucketValue.objects.create(
            bucket=bucket,
            xvalue=number + 1,
            yvalue=number,
            category=f'A very long category label number {number}',
        )

    image = matplotlib.image.imread(
        io.BytesIO(to_bytes_io(render(bucket, mode='dark')))
    )
    edges = [image[:3], image[-3:], image[:, :3], image[:, -3:]]
    assert all((edge == image[0, 0]).all() for edge in edges)


def test_both_modes_draw_with_the_same_chart_color():
    with override_settings(INSIGHTS_THEME={'accent': '#16a34a'}):
        assert (
            theme.chart_colors('light')['primary']
            == theme.chart_colors('dark')['primary']
        )


def test_a_wrong_dpi_falls_back_to_the_default():
    for dpi in (0, -5, 'high', True, None):
        with override_settings(INSIGHTS_CHART_DPI=dpi):
            assert charts.chart_dpi() == DEFAULT_DPI
    with override_settings(INSIGHTS_CHART_DPI=72):
        assert charts.chart_dpi() == 72
