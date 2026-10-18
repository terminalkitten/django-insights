import pytest
from django.core.checks import Warning as CheckWarning
from django.test import override_settings
from django.urls import reverse

from django_insights import checks, theme
from django_insights.charts import get_theme
from django_insights.palettes import ACCENTS, BASES
from tests.test_views import get_html

pytestmark = pytest.mark.django_db(databases=['default', 'insights'])


def lightness(color):
    return int(color[1:3], 16) + int(color[3:5], 16) + int(color[5:7], 16)


def test_without_settings_the_basecoat_defaults_are_used():
    assert theme.palette('light') == theme.DEFAULTS['light']
    assert theme.css_overrides() == ''
    assert theme.stylesheet() == 'insights/css/vega.css'
    assert theme.problems() == []


def test_the_palettes_are_complete_and_valid():
    assert theme.BASE_NAMES == (
        'neutral',
        'stone',
        'zinc',
        'mauve',
        'olive',
        'mist',
        'taupe',
    )
    assert len(theme.ACCENT_NAMES) == 17
    for base in BASES.values():
        for colors in base.values():
            assert set(colors) == set(theme.KEYS)
            assert all(theme.HEX.match(color) for color in colors.values())
    for accent in ACCENTS.values():
        for colors in accent.values():
            assert set(theme.CHART_KEYS) <= set(colors)
            assert set(colors) <= set(theme.KEYS)
            assert all(theme.HEX.match(color) for color in colors.values())


@override_settings(INSIGHTS_THEME='blue')
def test_an_accent_name_is_the_shadcn_theme_on_the_neutral_base():
    light, dark = theme.palette('light'), theme.palette('dark')

    assert light['primary'] == ACCENTS['blue']['light']['primary']
    assert dark['primary'] == ACCENTS['blue']['dark']['primary']
    assert [light[key] for key in theme.CHART_KEYS] == [
        ACCENTS['blue']['light'][key] for key in theme.CHART_KEYS
    ]
    assert light['background'] == BASES['neutral']['light']['background']
    assert '--chart-3:' in theme.css_overrides()


@override_settings(INSIGHTS_THEME='zinc')
def test_a_base_name_is_the_shadcn_base_color():
    assert theme.palette('dark')['card'] == BASES['zinc']['dark']['card']
    assert theme.palette('light')['muted'] == BASES['zinc']['light']['muted']
    assert theme.palette('dark')['card'] != theme.DEFAULTS['dark']['card']


@override_settings(INSIGHTS_THEME={'base': 'stone', 'accent': 'rose'})
def test_a_base_and_an_accent_combine():
    palette = theme.palette('light')

    assert palette['background'] == BASES['stone']['light']['background']
    assert palette['primary'] == ACCENTS['rose']['light']['primary']
    assert palette['chart_3'] == ACCENTS['rose']['light']['chart_3']


@override_settings(INSIGHTS_THEME={'accent': '#16A34A'})
def test_any_hex_color_is_an_accent_with_a_chart_ramp():
    light, dark = theme.palette('light'), theme.palette('dark')

    assert light['primary'] == light['chart_3'] == '#16a34a'
    assert dark['primary'] == '#16a34a'
    ramp = [lightness(light[key]) for key in theme.CHART_KEYS]
    assert ramp == sorted(ramp, reverse=True)
    assert light['sidebar_primary'] == '#16a34a'


@override_settings(
    INSIGHTS_THEME={
        'base': 'zinc',
        'accent': 'green',
        'dark': {'card': '#101010', 'primary': '#ffffff'},
    }
)
def test_your_colors_win_over_the_theme():
    assert theme.palette('dark')['card'] == '#101010'
    assert theme.palette('dark')['primary'] == '#ffffff'
    assert theme.palette('light')['primary'] == ACCENTS['green']['light']['primary']


@override_settings(INSIGHTS_THEME={'dark': {'card': '#101010'}})
def test_the_charts_use_the_colors_of_the_dashboard():
    colors = get_theme('dark')

    assert colors.face == colors.edge == theme.palette('dark')['card'] == '#101010'
    assert colors.tick == theme.palette('dark')['foreground']
    assert get_theme('light').face == theme.palette('light')['card']


@override_settings(INSIGHTS_THEME='blue')
def test_the_chart_color_is_the_middle_of_the_ramp_in_light_and_dark():
    assert get_theme('light').primary == theme.palette('light')['chart_3']
    assert get_theme('dark').primary == theme.palette('dark')['chart_3']


@pytest.mark.parametrize('name', [*theme.ACCENT_NAMES, *theme.BASE_NAMES])
def test_every_shadcn_theme_renders_a_palette_and_chart_colors(name):
    with override_settings(INSIGHTS_THEME=name):
        for mode in theme.MODES:
            assert set(theme.palette(mode)) == set(theme.KEYS)
            assert theme.HEX.match(get_theme(mode).primary)
        assert theme.problems() == []


@override_settings(
    INSIGHTS_THEME={
        'light': {
            'card': 'red',
            'border': '#fff;}body{display:none',
            'nope': '#000000',
        },
        'neon': {'card': '#000000'},
        'base': ['zinc'],
    }
)
def test_values_that_are_not_a_hex_color_are_ignored_and_never_reach_the_css():
    assert theme.palette('light') == theme.DEFAULTS['light']
    assert theme.css_overrides() == ''
    assert len(theme.problems()) == 5


def test_a_color_with_a_trailing_newline_is_not_a_hex_color():
    assert theme.HEX.match('#ffffff')
    assert not theme.HEX.match('#ffffff\n')


@override_settings(INSIGHTS_THEME={'accent': '#16a34a\n'})
def test_an_accent_with_a_trailing_newline_is_ignored():
    assert theme.css_overrides() == ''
    assert [check_id for check_id, _ in theme.problems()] == ['insights.W008']


@override_settings(INSIGHTS_THEME='chartreuse', INSIGHTS_STYLE='neon')
def test_a_wrong_style_or_theme_falls_back_and_is_reported():
    assert theme.stylesheet() == 'insights/css/vega.css'
    assert theme.palette('light') == theme.DEFAULTS['light']
    assert {check_id for check_id, _ in theme.problems()} == {
        'insights.W007',
        'insights.W008',
    }


@override_settings(INSIGHTS_THEME=42)
def test_a_theme_that_is_not_a_name_or_a_dict_is_ignored_and_reported():
    assert theme.palette('dark') == theme.DEFAULTS['dark']
    assert [check_id for check_id, _ in theme.problems()] == ['insights.W009']


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
    assert f'--primary:{ACCENTS["green"]["light"]["primary"]};' in html
    assert f'--chart-3:{ACCENTS["green"]["light"]["chart_3"]};' in html


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


@override_settings(INSIGHTS_THEME='zinc')
def test_a_color_that_differs_in_one_mode_is_written_for_both_modes():
    assert theme.palette('light')['foreground'] != theme.DEFAULTS['light']['foreground']
    assert theme.palette('dark')['foreground'] == theme.DEFAULTS['dark']['foreground']

    light, dark = theme.css_overrides().split('.dark')
    assert f'--foreground:{theme.palette("light")["foreground"]};' in light
    assert f'--foreground:{theme.palette("dark")["foreground"]};' in dark
