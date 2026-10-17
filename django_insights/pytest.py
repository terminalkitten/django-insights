from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest


def find_insight(label: str) -> Callable[..., Any]:
    """The function behind a registered insight, by name or by module.name"""
    from django_insights.registry import registry

    registry.autodiscover_insights()
    matches = [
        (module, getattr(func, '__wrapped__', func))
        for module, name, _, func in registry.registered_insights
        if label in (name, f'{module}.{name}')
    ]
    if not matches:
        raise LookupError(
            f"No insight named '{label}', is there an insights.py with that function?"
        )
    if len(matches) > 1:
        modules = ', '.join(module for module, _ in matches)
        raise LookupError(
            f"Several insights are named '{label}' ({modules}), use module.name"
        )
    return matches[0][1]


@pytest.fixture
def insights_query(request: pytest.FixtureRequest) -> Callable[..., Any]:
    """The insight function named by the marker, or by the test (test_<name>)"""
    marker = request.node.get_closest_marker('insights')
    if marker and marker.args:
        label = marker.args[0]
    else:
        name = getattr(request.node, 'originalname', request.node.name)
        label = name.removeprefix('test_')

    try:
        return find_insight(label)
    except LookupError as error:
        message = str(error)

    pytest.fail(message, pytrace=False)


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        'markers',
        "insights(name=None): test of an insight, defaults to the test name without 'test_'",
    )
