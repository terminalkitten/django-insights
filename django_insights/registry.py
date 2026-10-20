from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.db import transaction
from django.utils.module_loading import autodiscover_modules
from tqdm import tqdm

from django_insights.database import database_entry

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


@dataclass
class InsightFailure:
    module: str
    label: str
    error: Exception


class InsightRegistry:
    registered_insights: list[tuple[str, str, str | None, Callable[..., None]]]

    def __init__(self) -> None:
        self.registered_insights = []

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

    def collect_insights(self) -> list[InsightFailure]:
        """Run every insight, a failing insight is reported and the others still run"""
        failures = []
        progress_iterator = tqdm(
            self.registered_insights, desc='Collect insights', disable=None
        )

        for module, name, question, metric in progress_iterator:
            progress_iterator.set_description(
                desc=f"Create insights for {module}.{name}: {question}", refresh=True
            )

            started = time.perf_counter()
            try:
                with transaction.atomic(using=database_entry):
                    metric()
            except Exception as error:
                logger.exception('Insight %s.%s failed', module, name)
                failures.append(InsightFailure(module, name, error))
            else:
                logger.debug(
                    'Insight %s.%s collected in %.2fs',
                    module,
                    name,
                    time.perf_counter() - started,
                )

            progress_iterator.set_description(desc="Done!")

        return failures


registry = InsightRegistry()
