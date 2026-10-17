import pytest
from django.core import management

from django_insights.metrics import metrics
from django_insights.models import Bucket
from django_insights.registry import registry
from project.testapp.users.models import AppUser
from tests.utils import SEED_MESSAGES, SEED_USERS


@pytest.fixture
def collected():
    management.call_command(
        'seed_db', users=SEED_USERS, messages=SEED_MESSAGES, verbosity=0
    )
    registry.autodiscover_insights()
    metrics.collect(reset=True)


@pytest.fixture
def viewer_client(client):
    client.force_login(AppUser.objects.create(email='viewer@example.com'))
    return client


@pytest.fixture
def bucket(collected):
    return Bucket.objects.earliest('pk')
