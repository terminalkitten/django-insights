import pytest
from django.core.checks import Warning as CheckWarning
from django.test import override_settings
from django.urls import reverse

from django_insights import checks, theme
from django_insights.charts import get_theme
from tests.test_views import get_html

pytestmark = pytest.mark.django_db(databases=['default', 'insights'])


def lightness(color):
    return int(color[1:3], 16) + int(color[3:5], 16) + int(color[5:7], 16)


def test_without_settings_the_basecoat_defaults_are_used():
    assert theme.palette('light') == theme.DEFAULTS['light']
    assert theme.css_overrides() == ''
    assert theme.stylesheet() == 'insights/css/vega.css'
    assert theme.problems() == []


@override_settings(INSIGHTS_THEME={'accent': '#16A34A'})
def test_one_accent_color_sets_the_primary_color_and_a_chart_ramp():
    light, dark = theme.palette('light'), theme.palette('dark')

    assert light['primary'] == light['chart_3'] == '#16a34a'
    assert dark['chart_3'] == '#16a34a'
    assert lightness(dark['primary']) > lightness(light['primary'])
    ramp = [lightness(light[key]) for key in theme.CHART_KEYS]
    assert ramp == sorted(ramp, reverse=True)
    assert light['background'] == theme.DEFAULTS['light']['background']


@override_settings(
    INSIGHTS_THEME={
        'accent': '#16a34a',
        'dark': {'card': '#101010', 'primary': '#ffffff'},
    }
)
def test_your_colors_win_over_the_accent():
    assert theme.palette('dark')['card'] == '#101010'
    assert theme.palette('dark')['primary'] == '#ffffff'
    assert theme.palette('light')['primary'] == '#16a34a'


@override_settings(INSIGHTS_THEME={'dark': {'card': '#101010'}})
def test_the_charts_use_the_colors_of_the_dashboard():
    colors = get_theme('dark')

    assert colors.face == colors.edge == theme.palette('dark')['card'] == '#101010'
    assert colors.tick == theme.palette('dark')['foreground']
    assert get_theme('light').face == theme.palette('light')['card']


@override_settings(INSIGHTS_THEME='blue')
def test_the_chart_color_is_the_middle_of_the_ramp_in_light_and_the_lightest_in_dark():
    assert get_theme('light').primary == theme.palette('light')['chart_3']
    assert get_theme('dark').primary == theme.palette('dark')['chart_1']


@override_settings(
    INSIGHTS_THEME={
        'light': {
            'card': 'red',
            'border': '#fff;}body{display:none',
            'nope': '#000000',
        },
        'neon': {'card': '#000000'},
    }
)
def test_values_that_are_not_a_hex_color_are_ignored_and_never_reach_the_css():
    assert theme.palette('light') == theme.DEFAULTS['light']
    assert theme.css_overrides() == ''
    assert len(theme.problems()) == 4


@override_settings(INSIGHTS_THEME='chartreuse', INSIGHTS_STYLE='neon')
def test_a_wrong_style_or_preset_falls_back_and_is_reported():
    assert theme.stylesheet() == 'insights/css/vega.css'
    assert theme.palette('light') == theme.DEFAULTS['light']
    assert {check_id for check_id, _ in theme.problems()} == {
        'insights.W007',
        'insights.W008',
    }


@override_settings(INSIGHTS_STYLE='sera')
def test_the_style_selects_the_stylesheet():
    assert theme.stylesheet() == 'insights/css/sera.css'


def test_the_fingerprint_follows_the_colors():
    default = theme.fingerprint()
    with override_settings(INSIGHTS_THEME='pink'):
        assert theme.fingerprint() != default
    assert theme.fingerprint() == default


def test_every_style_has_a_compiled_stylesheet():
    from django.contrib.staticfiles import finders

    for name in theme.STYLES:
        assert finders.find(f'insights/css/{name}.css')


@override_settings(INSIGHTS_STYLE='nova', INSIGHTS_THEME='green')
def test_the_dashboard_loads_the_style_and_sets_the_colors(collected, viewer_client):
    html = get_html(viewer_client, reverse('insights:insight_dashboard'))

    assert 'insights/css/nova.css' in html
    assert '--primary:#16a34a;' in html
    assert '--chart-3:#16a34a;' in html


def test_the_dashboard_has_no_inline_style_without_colors(collected, viewer_client):
    html = get_html(viewer_client, reverse('insights:insight_dashboard'))
    assert '<style>' not in html


@override_settings(
    INSIGHTS_CHART_LIGHT_PRIMARY_COLOR='#ff0000',
    INSIGHTS_STYLE='nope',
)
def test_removed_and_wrong_settings_are_warnings_that_never_block():
    messages = checks.check_theme(app_configs=None, databases=None)

    assert all(isinstance(message, CheckWarning) for message in messages)
    assert {message.id for message in messages} == {'insights.W007', 'insights.W010'}


@override_settings(INSIGHTS_THEME='pink')
def test_a_preset_name_is_the_same_as_its_accent_color():
    assert theme.palette('light')['primary'] == theme.PRESETS['pink']
    assert theme.palette('light') == theme.from_accent(theme.PRESETS['pink'])[
        'light'
    ] | {
        key: value
        for key, value in theme.DEFAULTS['light'].items()
        if key not in theme.from_accent(theme.PRESETS['pink'])['light']
    }


@override_settings(INSIGHTS_THEME=42)
def test_a_theme_that_is_not_a_name_or_a_dict_is_ignored_and_reported():
    assert theme.palette('dark') == theme.DEFAULTS['dark']
    assert [check_id for check_id, _ in theme.problems()] == ['insights.W009']


def test_every_preset_is_a_valid_color():
    assert all(theme.HEX.match(color) for color in theme.PRESETS.values())
