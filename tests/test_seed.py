import pytest
from django.core import management
from django.db.models import Count, Sum
from django.db.models.functions import ExtractWeekDay

from project.testapp.models import Channel, Membership, Message, Report, Workspace
from project.testapp.users.models import AppUser

pytestmark = pytest.mark.django_db


def seed(**options):
    management.call_command('seed_db', verbosity=0, **options)


def fingerprint():
    return (
        AppUser.objects.filter(invited_by__isnull=False).count(),
        Message.objects.aggregate(tokens=Sum('tokens'), cost=Sum('cost')),
    )


def test_the_seed_creates_what_it_is_asked_for():
    seed(users=40, messages=120)

    assert AppUser.objects.count() == 40
    assert Message.objects.count() == 120
    for model in (Workspace, Membership, Channel, Report):
        assert model.objects.exists()


def test_the_same_seed_gives_the_same_data():
    seed(users=40, messages=120, seed=7)
    first = fingerprint()
    seed(users=40, messages=120, seed=7)
    assert fingerprint() == first

    seed(users=40, messages=120, seed=8)
    assert fingerprint() != first


def test_seeding_again_replaces_the_data():
    seed(users=20, messages=60)
    seed(users=25, messages=70)
    assert (AppUser.objects.count(), Message.objects.count()) == (25, 70)


def test_the_data_has_the_shape_the_demo_needs():
    seed(users=150, messages=1500)

    users = AppUser.objects.count()
    invited = AppUser.objects.filter(invited_by__isnull=False).count()
    assert 0.25 < invited / users < 0.55

    weekdays = dict(
        Message.objects.annotate(day=ExtractWeekDay('created_at'))
        .values_list('day')
        .annotate(total=Count('pk'))
    )
    weekend = weekdays.get(1, 0) + weekdays.get(7, 0)
    assert weekend / Message.objects.count() < 0.1
    assert weekdays[3] > 3 * weekend

    per_author = sorted(
        Message.objects.filter(author__isnull=False)
        .values_list('author')
        .annotate(total=Count('pk'))
        .values_list('total', flat=True),
        reverse=True,
    )
    top_tenth = per_author[: len(per_author) // 10]
    assert sum(top_tenth) / sum(per_author) > 0.4


def test_the_ai_share_grows_over_time():
    seed(users=150, messages=1500)

    messages = list(
        Message.objects.order_by('created_at').values_list('is_ai', flat=True)
    )
    early = messages[: len(messages) * 2 // 5]
    late = messages[len(messages) * 3 // 5 :]
    assert sum(late) / len(late) > sum(early) / len(early)


def test_the_ai_models_have_their_own_price_per_token():
    seed(users=150, messages=1500)

    rates = {
        model: cost / tokens
        for model, tokens, cost in Message.objects.filter(is_ai=True)
        .values_list('model')
        .annotate(tokens=Sum('tokens'), cost=Sum('cost'))
        .values_list('model', 'tokens', 'cost')
    }
    assert rates['assistant-large'] > 5 * rates['assistant-small']
