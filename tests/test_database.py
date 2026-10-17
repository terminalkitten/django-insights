import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from django_insights.database import Router, check_settings
from django_insights.models import Bucket, Counter
from project.settings.test import DATABASES
from project.testapp.users.models import AppUser

router = Router()


def test_check_settings_requires_insights_database():
    without_insights = {k: v for k, v in DATABASES.items() if k != 'insights'}
    with (
        override_settings(DATABASES=without_insights),
        pytest.raises(ImproperlyConfigured),
    ):
        check_settings()


def test_check_settings_passes_with_insights_database():
    check_settings()


@pytest.mark.parametrize(
    ('model', 'alias'), [(Counter, 'insights'), (Bucket, 'insights'), (AppUser, None)]
)
def test_router_reads_and_writes(model, alias):
    assert router.db_for_read(model) == alias
    assert router.db_for_write(model) == alias


@pytest.mark.parametrize(
    ('db', 'app_label', 'allowed'),
    [
        ('insights', 'insights', True),
        ('default', 'insights', False),
        ('default', 'users', None),
    ],
)
def test_router_allow_migrate(db, app_label, allowed):
    assert router.allow_migrate(db, app_label) is allowed


def test_router_allow_relation():
    assert router.allow_relation(Counter(), Bucket()) is True
    assert router.allow_relation(AppUser(), AppUser()) is None
