from __future__ import annotations

from typing import Any, Callable

from django.utils.module_loading import autodiscover_modules
from tqdm import tqdm

from django_insights.utils import read_only_mode


class InsightRegistry:
    registered_insights: list[tuple[str, str, str, Callable[[Any], Any]]] = list()

    @staticmethod
    def autodiscover_insights():
        autodiscover_modules("insights")

    def register_insight(
        self,
        label: str,
        module: str,
        question: str,
        func: Callable[[Any], Any],
    ):
        self.registered_insights.append((module, label, question, func))

    def collect_insights(self):
        progress_iterator = tqdm(self.registered_insights, desc='Collect insights')

        for module, name, question, metric in progress_iterator:
            progress_iterator.set_description(
                desc=f"Create insights for {module}.{name}", refresh=True
            )
            with read_only_mode(metric) as read_only_metric:
                read_only_metric()

            progress_iterator.set_description(desc="Done!")


registry = InsightRegistry()
