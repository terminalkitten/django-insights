import pytest

from django_insights.models import Counter
from django_insights.pytest import find_insight
from django_insights.registry import registry

pytestmark = pytest.mark.django_db(databases=['default', 'insights'])


@pytest.mark.insights
def test_count_users(insights_query):
    assert insights_query() == 0


@pytest.mark.insights('count_messages')
def test_the_marker_names_the_insight(insights_query):
    assert insights_query() == 0


def test_an_insight_can_be_found_by_name():
    assert find_insight('count_users')() == 0


def test_an_insight_can_be_found_by_module_and_name():
    assert find_insight('project.testapp.users.insights.count_users')() == 0


def test_the_insight_is_the_original_function_and_saves_nothing():
    find_insight('count_users')()
    assert not Counter.objects.exists()


def test_an_unknown_insight_is_reported():
    with pytest.raises(LookupError, match="No insight named 'nope'"):
        find_insight('nope')


def test_an_ambiguous_name_is_reported(monkeypatch):
    registry.autodiscover_insights()
    insights = [
        ('first.insights', 'total', 'q', lambda: 1),
        ('second.insights', 'total', 'q', lambda: 2),
    ]
    monkeypatch.setattr(registry, 'registered_insights', insights)

    with pytest.raises(LookupError, match=r'first\.insights, second\.insights'):
        find_insight('total')
    assert find_insight('second.insights.total')() == 2
