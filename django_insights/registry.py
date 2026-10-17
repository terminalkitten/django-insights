from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar

from django.utils.module_loading import autodiscover_modules
from tqdm import tqdm


class InsightRegistry:
    registered_insights: ClassVar[
        list[tuple[str, str, str | None, Callable[..., None]]]
    ] = []

    @staticmethod
    def autodiscover_insights() -> None:
        autodiscover_modules("insights")

    def register_insight(
        self,
        label: str,
        module: str,
        question: str | None,
        func: Callable[..., None],
    ) -> None:
        self.registered_insights.append((module, label, question, func))

    def collect_insights(self) -> None:
        progress_iterator = tqdm(self.registered_insights, desc='Collect insights')

        for module, name, question, metric in progress_iterator:
            progress_iterator.set_description(
                desc=f"Create insights for {module}.{name}: {question}", refresh=True
            )

            metric()

            progress_iterator.set_description(desc="Done!")


registry = InsightRegistry()
