import pytest
from django.test import override_settings

from django_insights.checks import (
    check_charts,
    check_dashboard_permissions,
    check_database,
    check_media_cache,
    check_renamed_settings,
)
from tests.utils import AllowAll, DenyAll, NoMethod


def ids(check):
    return [message.id for message in check(app_configs=None, databases=None)]


@pytest.mark.parametrize('permissions', [None, [], [AllowAll], (AllowAll, DenyAll)])
def test_valid_permissions_pass(permissions):
    with override_settings(INSIGHTS_DASHBOARD_PERMISSIONS=permissions):
        assert ids(check_dashboard_permissions) == []


def test_permissions_must_be_a_list():
    with override_settings(INSIGHTS_DASHBOARD_PERMISSIONS=AllowAll):
        assert ids(check_dashboard_permissions) == ['insights.W001']


@pytest.mark.parametrize('entry', [NoMethod, AllowAll(), 'tests.utils.AllowAll'])
def test_every_invalid_entry_is_reported(entry):
    with override_settings(INSIGHTS_DASHBOARD_PERMISSIONS=[AllowAll, entry]):
        assert ids(check_dashboard_permissions) == ['insights.W002']


@pytest.mark.parametrize(
    ('enabled', 'root', 'expected'),
    [
        (False, None, []),
        (True, 'charts', []),
        (True, None, ['insights.W003']),
        (True, '', ['insights.W003']),
    ],
)
def test_media_cache_requires_a_root(enabled, root, expected):
    with override_settings(
        INSIGHTS_CHARTS_USE_MEDIA_CACHE=enabled, INSIGHTS_MEDIA_CACHE_ROOT=root
    ):
        assert ids(check_media_cache) == expected


def test_a_configured_project_has_no_database_warnings():
    assert ids(check_database) == []


def test_missing_insights_database_and_router_are_reported():
    databases = {
        'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}
    }
    with override_settings(DATABASES=databases, DATABASE_ROUTERS=[]):
        assert ids(check_database) == ['insights.W004', 'insights.W005']


def test_renamed_settings_are_reported():
    with override_settings(INSIGHT_DASHBOARD_PERMISSIONS=[DenyAll]):
        assert ids(check_renamed_settings) == ['insights.W006']
    assert ids(check_renamed_settings) == []


@pytest.mark.parametrize('theme', ['light', 'dark'])
def test_a_known_default_theme_passes(theme):
    with override_settings(INSIGHTS_DEFAULT_THEME=theme):
        assert ids(check_charts) == []


def test_an_unknown_default_theme_is_reported():
    with override_settings(INSIGHTS_DEFAULT_THEME='neon'):
        assert ids(check_charts) == ['insights.W011']


@pytest.mark.parametrize('dpi', [0, -1, 'high', 1.5, True])
def test_a_dpi_that_is_not_a_positive_number_is_reported(dpi):
    with override_settings(INSIGHTS_CHART_DPI=dpi):
        assert ids(check_charts) == ['insights.W012']
