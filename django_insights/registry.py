from __future__ import annotations

from typing import Any, Callable

from django.utils.module_loading import autodiscover_modules
from tqdm import tqdm


class InsightRegistry:
    registered_insights: list[tuple[str, str, str, Callable[[Any], Any]]] = list()

    @staticmethod
    def autodiscover_insights():
        autodiscover_modules("insights")

    def register_insight(
        self,
        label: str,
        app: str,
        question: str,
        func: Callable[[Any], Any],
    ):
        self.registered_insights.append((app, label, question, func))

    def collect_insights(self):
        progress_iterator = tqdm(self.registered_insights, desc='Collect insights')

        for app, name, question, metric in progress_iterator:
            progress_iterator.set_description(
                desc=f"Create insights for {app}.{name}", refresh=True
            )
            metric()

        progress_iterator.set_description(desc="Done!")


registry = InsightRegistry()
