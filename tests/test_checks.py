import pytest
from django.test import override_settings

from django_insights.checks import check_dashboard_permissions, check_media_cache
from tests.utils import AllowAll, DenyAll, NoMethod


@pytest.mark.parametrize('permissions', [None, [], [AllowAll], (AllowAll, DenyAll)])
def test_valid_permissions_pass(permissions):
    with override_settings(INSIGHT_DASHBOARD_PERMISSIONS=permissions):
        assert check_dashboard_permissions(app_configs=None, databases=None) == []


def test_permissions_must_be_a_list():
    with override_settings(INSIGHT_DASHBOARD_PERMISSIONS=AllowAll):
        errors = check_dashboard_permissions(app_configs=None, databases=None)
    assert [error.id for error in errors] == ['insights.E001']


@pytest.mark.parametrize('entry', [NoMethod, AllowAll(), 'tests.utils.AllowAll'])
def test_every_invalid_entry_is_reported(entry):
    with override_settings(INSIGHT_DASHBOARD_PERMISSIONS=[AllowAll, entry]):
        errors = check_dashboard_permissions(app_configs=None, databases=None)
    assert [error.id for error in errors] == ['insights.E002']


@pytest.mark.parametrize(
    ('enabled', 'root', 'ids'),
    [
        (False, None, []),
        (True, 'charts', []),
        (True, None, ['insights.E003']),
        (True, '', ['insights.E003']),
    ],
)
def test_media_cache_requires_a_root(enabled, root, ids):
    with override_settings(
        INSIGHT_CHARTS_USE_MEDIA_CACHE=enabled, INSIGHT_MEDIA_CACHE_ROOT=root
    ):
        errors = check_media_cache(app_configs=None, databases=None)
    assert [error.id for error in errors] == ids
