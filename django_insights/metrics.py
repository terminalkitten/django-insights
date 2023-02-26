from __future__ import annotations

import functools

from django_insights.choices import BucketType
from django_insights.metrics_types import (
    CounterType,
    GaugeType,
    ScatterPlotType,
    TimeSeriesType,
)
from django_insights.models import App, Bucket, BucketValue, Counter, Gauge
from django_insights.registry import registry


class InsightMetrics:
    """Auto-generate metrics from mulitple apps at once"""

    create_counters: list[Counter] = []
    create_gauges: list[Gauge] = []
    create_bucket_values: list[BucketValue] = []

    apps: dict[str, App] = {}

    def __init__(self) -> None:
        """Reset current dataset if metrics are generated"""
        Counter.objects.all().delete()
        Gauge.objects.all().delete()
        Bucket.objects.all().delete()
        BucketValue.objects.all().delete()

    def get_memoized_app(self, name: str) -> App:
        """Memoize apps so we reduce query count"""
        if app := self.apps.get(name):
            return app

        # get or create new app
        app, _ = App.objects.get_or_create(name=name)
        self.apps.update({name: app})

        return app

    def get_app(self, func) -> tuple[str, App]:
        label = func.__name__
        app_name = func.__module__

        app = self.get_memoized_app(name=app_name)

        return label, app

    def counter(self, question: str = None, desc: str = None):
        """Decorator to collect Counter metrics"""

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
                app=app.name,
                question=question,
                func=inner,
            )

            return None

        return decorator

    def gauge(self, question: str = None, desc: str = None):
        """Decorator to collect Gauge metrics"""

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
                app=app.name,
                question=question,
                func=inner,
            )

            return None

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
        """Decorator to collect TimeSeries metrics"""

        def decorator(func):
            label, app = self.get_app(func)

            @functools.wraps(func)
            def inner(*args, **kwargs):
                ts_type = TimeSeriesType(values=func(*args, **kwargs))

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
                app=app.name,
                question=question,
                func=inner,
            )

            return None

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
        """Decorator to collect Scatterplot metrics"""

        def decorator(func):
            label, app = self.get_app(func)

            @functools.wraps(func)
            def inner(*args, **kwargs):
                scp_type = ScatterPlotType(values=func(*args, **kwargs))

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
                        timestamp=row.timestamp,
                        bucket=bucket,
                    )
                    self.create_bucket_values.append(bucket_value)

            registry.register_insight(
                label=label,
                app=app.name,
                question=question,
                func=inner,
            )

            return None

        return decorator

    def collect(self):
        registry.collect_insights()

        Counter.objects.bulk_create(self.create_counters)
        Gauge.objects.bulk_create(self.create_gauges)
        BucketValue.objects.bulk_create(self.create_bucket_values)


metrics = InsightMetrics()
