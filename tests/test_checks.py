import pytest
from django.test import override_settings

from django_insights.checks import check_dashboard_permissions
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
