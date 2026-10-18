from __future__ import annotations

import functools
import importlib
import uuid
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from django.db import IntegrityError, transaction

from django_insights.choices import BucketType
from django_insights.database import database_entry
from django_insights.exceptions import InsightsError
from django_insights.metrics_types import (
    BarChartAnswer,
    BarChartResult,
    BarChartType,
    CounterType,
    GaugeType,
    ScatterPlotAnswer,
    ScatterPlotResult,
    ScatterPlotType,
    TimeSeriesAnswer,
    TimeSeriesResult,
    TimeSeriesType,
)
from django_insights.models import App, Bucket, BucketValue, Counter, Gauge
from django_insights.registry import InsightFailure, registry
from django_insights.utils import rebuild_chart_media_cache

__all__ = ['InsightMetrics', 'metrics']

P = ParamSpec('P')
TrendFunc = Callable[[], TimeSeriesResult]
TREND_POINTS = 60
TimeSeriesReturn = TypeVar('TimeSeriesReturn', bound=TimeSeriesResult)
ScatterPlotReturn = TypeVar('ScatterPlotReturn', bound=ScatterPlotResult)
BarChartReturn = TypeVar('BarChartReturn', bound=BarChartResult)


def collect_trend(trend: TrendFunc | None) -> list[float]:
    """The values of a trend series, oldest first, the latest points only"""
    if trend is None:
        return []
    return [float(value) for _, value in trend()][-TREND_POINTS:]


class InsightMetrics:
    """Auto-generate metrics from multiple apps at once"""

    create_counters: list[Counter]
    create_gauges: list[Gauge]
    create_bucket_values: list[BucketValue]
    apps: dict[str, App]

    def __init__(self) -> None:
        self.reset_state()

    def reset_state(self) -> None:
        self.create_counters = []
        self.create_gauges = []
        self.create_bucket_values = []
        self.apps = {}

    def delete_metrics(self) -> None:
        """Reset current dataset if metrics are generated"""
        Counter.objects.all().delete()
        Gauge.objects.all().delete()
        Bucket.objects.all().delete()
        BucketValue.objects.all().delete()

    def get_memoized_app(self, module: str, label: str | None = None) -> App:
        """Memoize apps so we reduce query count"""
        if app := self.apps.get(module):
            return app

        # get or create new app
        app, _ = App.objects.get_or_create(
            module=module,
            defaults={
                'label': label,
                'uuid': uuid.uuid5(uuid.NAMESPACE_URL, f'django-insights:{module}'),
            },
        )
        self.apps.update({module: app})

        return app

    def get_app(self, func: Callable[..., object]) -> tuple[str, App]:
        """Describe the app of an insight"""

        label = getattr(func, '__name__', repr(func))
        module = getattr(func, '__module__', '')
        insights_module = importlib.import_module(module)

        app_label = getattr(insights_module, 'label', None)
        return label, App(module=module, label=app_label)

    def counter(
        self,
        question: str | None = None,
        desc: str | None = None,
        trend: TrendFunc | None = None,
    ) -> Callable[[Callable[P, int]], Callable[P, int]]:
        """Decorator to collect Counter metrics"""

        def decorator(func: Callable[P, int]) -> Callable[P, int]:
            label, app = self.get_app(func)

            @functools.wraps(func)
            def inner(*args: P.args, **kwargs: P.kwargs) -> None:
                counter_type = CounterType(value=func(*args, **kwargs))
                counter = Counter(
                    app=self.get_memoized_app(app.module, app.label),
                    label=label,
                    value=counter_type.value,
                    trend=collect_trend(trend),
                    question=question,
                    desc=desc,
                )
                self.create_counters.append(counter)

            registry.register_insight(
                label=label,
                module=app.module,
                question=question,
                func=inner,
            )

            return func

        return decorator

    def gauge(
        self,
        question: str | None = None,
        desc: str | None = None,
        trend: TrendFunc | None = None,
    ) -> Callable[[Callable[P, float]], Callable[P, float]]:
        """Decorator to collect Gauge metric"""

        def decorator(func: Callable[P, float]) -> Callable[P, float]:
            label, app = self.get_app(func)

            @functools.wraps(func)
            def inner(*args: P.args, **kwargs: P.kwargs) -> None:
                gauge_type = GaugeType(value=func(*args, **kwargs))
                gauge = Gauge(
                    app=self.get_memoized_app(app.module, app.label),
                    label=label,
                    value=gauge_type.value,
                    trend=collect_trend(trend),
                    question=question,
                    desc=desc,
                )
                self.create_gauges.append(gauge)

            registry.register_insight(
                label=label,
                module=app.module,
                question=question,
                func=inner,
            )

            return func

        return decorator

    def timeseries(
        self,
        question: str | None = None,
        desc: str | None = None,
        xlabel: str | None = None,
        xformat: str | None = None,
        ylabel: str | None = None,
        yformat: str | None = None,
        title: str | None = None,
    ) -> Callable[[Callable[P, TimeSeriesReturn]], Callable[P, TimeSeriesReturn]]:
        """
        Decorator to collect TimeSeries metrics

        """

        def decorator(
            func: Callable[P, TimeSeriesReturn],
        ) -> Callable[P, TimeSeriesReturn]:
            label, app = self.get_app(func)

            @functools.wraps(func)
            def inner(*args: P.args, **kwargs: P.kwargs) -> None:
                results = func(*args, **kwargs)
                ts_type = TimeSeriesType(
                    values=[TimeSeriesAnswer(*result) for result in results]
                )

                bucket = Bucket.objects.create(
                    app=self.get_memoized_app(app.module, app.label),
                    label=label,
                    question=question,
                    desc=desc,
                    xlabel=xlabel,
                    xformat=xformat,
                    ylabel=ylabel,
                    yformat=yformat,
                    title=title,
                    type=BucketType.TIMESERIES,
                )

                for row in ts_type.values:
                    bucket_value = BucketValue(
                        timestamp=row.timestamp, xvalue=row.xvalue, bucket=bucket
                    )
                    self.create_bucket_values.append(bucket_value)

            registry.register_insight(
                label=label,
                module=app.module,
                question=question,
                func=inner,
            )

            return func

        return decorator

    def scatterplot(
        self,
        question: str | None = None,
        desc: str | None = None,
        xlabel: str | None = None,
        xformat: str | None = None,
        ylabel: str | None = None,
        yformat: str | None = None,
        title: str | None = None,
    ) -> Callable[[Callable[P, ScatterPlotReturn]], Callable[P, ScatterPlotReturn]]:
        """
        Decorator to collect Scatterplot metrics

        """

        def decorator(
            func: Callable[P, ScatterPlotReturn],
        ) -> Callable[P, ScatterPlotReturn]:
            label, app = self.get_app(func)

            @functools.wraps(func)
            def inner(*args: P.args, **kwargs: P.kwargs) -> None:
                results = func(*args, **kwargs)
                scp_type = ScatterPlotType(
                    values=[ScatterPlotAnswer(*result) for result in results]
                )

                bucket = Bucket.objects.create(
                    app=self.get_memoized_app(app.module, app.label),
                    label=label,
                    question=question,
                    desc=desc,
                    xlabel=xlabel,
                    xformat=xformat,
                    ylabel=ylabel,
                    yformat=yformat,
                    title=title,
                    type=BucketType.SCATTERPLOT,
                )

                for row in scp_type.values:
                    bucket_value = BucketValue(
                        xvalue=row.xvalue,
                        yvalue=row.yvalue,
                        category=row.category,
                        bucket=bucket,
                    )
                    self.create_bucket_values.append(bucket_value)

            registry.register_insight(
                label=label,
                module=app.module,
                question=question,
                func=inner,
            )

            return func

        return decorator

    def barchart(
        self,
        question: str | None = None,
        desc: str | None = None,
        xlabel: str | None = None,
        xformat: str | None = None,
        ylabel: str | None = None,
        yformat: str | None = None,
        title: str | None = None,
    ) -> Callable[[Callable[P, BarChartReturn]], Callable[P, BarChartReturn]]:
        """
        Decorator to collect Barchart metrics

        """

        def decorator(func: Callable[P, BarChartReturn]) -> Callable[P, BarChartReturn]:
            label, app = self.get_app(func)

            @functools.wraps(func)
            def inner(*args: P.args, **kwargs: P.kwargs) -> None:
                results = func(*args, **kwargs)
                bar_type = BarChartType(
                    values=[BarChartAnswer(*result) for result in results]
                )

                bucket = Bucket.objects.create(
                    app=self.get_memoized_app(app.module, app.label),
                    label=label,
                    question=question,
                    desc=desc,
                    xlabel=xlabel,
                    xformat=xformat,
                    ylabel=ylabel,
                    yformat=yformat,
                    title=title,
                    type=BucketType.BARCHART,
                )

                for row in bar_type.values:
                    bucket_value = BucketValue(
                        xvalue=row.xvalue,
                        yvalue=row.yvalue,
                        category=row.category,
                        bucket=bucket,
                    )
                    self.create_bucket_values.append(bucket_value)

            registry.register_insight(
                label=label,
                module=app.module,
                question=question,
                func=inner,
            )

            return func

        return decorator

    def hbarchart(
        self,
        question: str | None = None,
        desc: str | None = None,
        xlabel: str | None = None,
        xformat: str | None = None,
        ylabel: str | None = None,
        yformat: str | None = None,
        title: str | None = None,
    ) -> Callable[[Callable[P, BarChartReturn]], Callable[P, BarChartReturn]]:
        """
        Decorator to collect Horizontal Barchart metrics

        """

        def decorator(func: Callable[P, BarChartReturn]) -> Callable[P, BarChartReturn]:
            label, app = self.get_app(func)

            @functools.wraps(func)
            def inner(*args: P.args, **kwargs: P.kwargs) -> None:
                results = func(*args, **kwargs)
                bar_type = BarChartType(
                    values=[BarChartAnswer(*result) for result in results]
                )

                bucket = Bucket.objects.create(
                    app=self.get_memoized_app(app.module, app.label),
                    label=label,
                    question=question,
                    desc=desc,
                    xlabel=xlabel,
                    xformat=xformat,
                    ylabel=ylabel,
                    yformat=yformat,
                    title=title,
                    type=BucketType.HBARCHART,
                )

                for row in bar_type.values:
                    bucket_value = BucketValue(
                        xvalue=row.xvalue,
                        yvalue=row.yvalue,
                        category=row.category,
                        bucket=bucket,
                    )
                    self.create_bucket_values.append(bucket_value)

            registry.register_insight(
                label=label,
                module=app.module,
                question=question,
                func=inner,
            )

            return func

        return decorator

    def collect(self, reset: bool = False) -> list[InsightFailure]:
        """Collect all insights in one transaction on the insights database"""
        self.reset_state()
        try:
            with transaction.atomic(using=database_entry):
                if reset:
                    self.delete_metrics()
                failures = registry.collect_insights()
                self.save_collected()
        finally:
            self.reset_state()

        rebuild_chart_media_cache()
        return failures

    def save_collected(self) -> None:
        try:
            Counter.objects.bulk_create(self.create_counters)
            Gauge.objects.bulk_create(self.create_gauges)
            BucketValue.objects.bulk_create(self.create_bucket_values)
        except IntegrityError as e:
            raise InsightsError(
                "Most likely you've redefined an insights method with the same name."
            ) from e


metrics = InsightMetrics()
