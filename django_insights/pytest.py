import inspect
from collections import namedtuple
from importlib import import_module
from typing import Callable
from unittest.mock import patch

import pytest

App = namedtuple('App', ('module'))


def register_insights_modules(*args, **kwargs) -> dict[str, Callable]:
    """
    Helper function to load insights functions into registry
    This way pytest can look them up and call them from a fixture,
    it also disables collecting parts with mocks

    Returns:
        dict[str, Callable]: registry with functions
    """
    from django.apps import apps

    registry: dict[str, Callable] = {}

    for app_config in apps.get_app_configs():
        for module_to_search in args:
            # Attempt to import the app's module.
            try:
                with patch('django_insights.metrics.InsightMetrics.get_app') as get_app:
                    get_app.return_value = ("foo", App(module="bar"))
                    mod = import_module("%s.%s" % (app_config.name, module_to_search))
                    functions = inspect.getmembers(mod, inspect.isfunction)
                    registry = {**registry, **dict(functions)}
            except Exception:
                continue

    return registry


registry = register_insights_modules("insights")


@pytest.fixture
def insights_query(request) -> Callable | None:
    """
    Returns insights_query fixture, this function
    resolves wrapped function from registry

    Args:
        request (_type_): Current calling context

    Returns:
        Callable | None: Return function to call query
    """
    if func := registry.get(request.node.name.replace("test_", "")):
        return func

    return None


def pytest_runtest_setup(item: pytest.Item) -> None:
    """
    Add insight fixture to insights marked tests

    Args:
        item (pytest.Item): pytest function description
    """
    marker = item.get_closest_marker("insights")
    if marker is None:
        return
    item.fixturenames.insert(0, 'insights_query')
