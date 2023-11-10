from __future__ import annotations

import functools
import importlib

from django.db import IntegrityError

from django_insights.choices import BucketType
from django_insights.metrics_types import (
    BarChartAnswer,
    BarChartType,
    CounterType,
    GaugeType,
    ScatterPlotAnswer,
    ScatterPlotType,
    TimeSeriesAnswer,
    TimeSeriesType,
)
from django_insights.models import App, Bucket, BucketValue, Counter, Gauge
from django_insights.registry import registry
from django_insights.utils import rebuild_chart_media_cache


class InsightMetrics:
    """Auto-generate metrics from multiple apps at once"""

    create_counters: list[Counter]
    create_gauges: list[Gauge]
    create_bucket_values: list[BucketValue]

    apps: dict[str, App] = {}

    def __init__(self) -> None:
        self.create_counters = []
        self.create_gauges = []
        self.create_bucket_values = []

    def delete_metrics(self) -> None:
        """Reset current dataset if metrics are generated"""
        Counter.objects.all().delete()
        Gauge.objects.all().delete()
        Bucket.objects.all().delete()
        BucketValue.objects.all().delete()

    def get_memoized_app(self, module: str, label: str = None) -> App:
        """Memoize apps so we reduce query count"""
        if app := self.apps.get(module):
            return app

        # get or create new app
        app, _ = App.objects.get_or_create(module=module, defaults={'label': label})
        self.apps.update({module: app})

        return app

    def get_app(self, func) -> tuple[str, App]:
        """
        Get memoized app

        """

        label = func.__name__
        module = func.__module__
        insights_module = importlib.import_module(module)

        app_label = getattr(insights_module, 'label', None)
        app = self.get_memoized_app(module=module, label=app_label)

        return label, app

    def counter(self, question: str = None, desc: str = None):
        """
        Decorator to collect Counter metrics

        """

        def decorator(func):
            label, app = self.get_app(func)

            @functools.wraps(func)
            def inner(*args, **kwargs):
                counter_type = CounterType(value=func(*args, **kwargs))
                counter = Counter(
                    app=app,
                    label=label,
                    value=counter_type.value,
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

    def gauge(self, question: str = None, desc: str = None):
        """
        Decorator to collect Gauge metric

        """

        def decorator(func):
            label, app = self.get_app(func)

            @functools.wraps(func)
            def inner(*args, **kwargs):
                gauge_type = GaugeType(value=func(*args, **kwargs))
                gauge = Gauge(
                    app=app,
                    label=label,
                    value=gauge_type.value,
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
        question: str = None,
        desc: str = None,
        xlabel: str = None,
        xformat: str = None,
        ylabel: str = None,
        yformat: str = None,
        title=None,
    ):
        """
        Decorator to collect TimeSeries metrics

        """

        def decorator(func):
            label, app = self.get_app(func)

            @functools.wraps(func)
            def inner(*args, **kwargs):
                results = func(*args, **kwargs)
                ts_type = TimeSeriesType(
                    values=[TimeSeriesAnswer(*result) for result in results]
                )

                bucket = Bucket.objects.create(
                    app=app,
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
        question: str = None,
        desc: str = None,
        xlabel: str = None,
        xformat: str = None,
        ylabel: str = None,
        yformat: str = None,
        title=None,
    ):
        """
        Decorator to collect Scatterplot metrics

        """

        def decorator(func):
            label, app = self.get_app(func)

            @functools.wraps(func)
            def inner(*args, **kwargs):
                results = func(*args, **kwargs)
                scp_type = ScatterPlotType(
                    values=[ScatterPlotAnswer(*result) for result in results]
                )

                bucket = Bucket.objects.create(
                    app=app,
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
        question: str = None,
        desc: str = None,
        xlabel: str = None,
        xformat: str = None,
        ylabel: str = None,
        yformat: str = None,
        title=None,
    ):
        """
        Decorator to collect Barchart metrics

        """

        def decorator(func):
            label, app = self.get_app(func)

            @functools.wraps(func)
            def inner(*args, **kwargs):
                results = func(*args, **kwargs)
                bar_type = BarChartType(
                    values=[BarChartAnswer(*result) for result in results]
                )

                bucket = Bucket.objects.create(
                    app=app,
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
        question: str = None,
        desc: str = None,
        xlabel: str = None,
        xformat: str = None,
        ylabel: str = None,
        yformat: str = None,
        title=None,
    ):
        """
        Decorator to collect Horizontal Barchart metrics

        """

        def decorator(func):
            label, app = self.get_app(func)

            @functools.wraps(func)
            def inner(*args, **kwargs):
                results = func(*args, **kwargs)
                bar_type = BarChartType(
                    values=[BarChartAnswer(*result) for result in results]
                )

                bucket = Bucket.objects.create(
                    app=app,
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

    def collect(self, reset: bool = False):
        """
        Collect insights

        """

        # Reset metrics
        self.delete_metrics() if reset else None

        # Break chart cache
        rebuild_chart_media_cache()

        # Collect insights
        registry.collect_insights()

        try:
            Counter.objects.bulk_create(self.create_counters)
            Gauge.objects.bulk_create(self.create_gauges)
            BucketValue.objects.bulk_create(self.create_bucket_values)

        except IntegrityError as e:
            print(
                "Something went wrong, most likely a you've redefined a insights method with the same name."
            )
            print("Stacktrace:", e)
            exit()


metrics = InsightMetrics()
