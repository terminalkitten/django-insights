import pytest

from django_insights.database import Router
from django_insights.models import Bucket, Counter
from project.testapp.users.models import AppUser

router = Router()


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
