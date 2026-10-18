import uuid

from django.db import models
from django.utils import timezone

from django_insights.choices import BucketType
from django_insights.database import database_entry
from django_insights.managers import BucketManager


class App(models.Model):
    """
    Apps that have insights

    """

    uuid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    module = models.CharField(max_length=254, unique=True)
    label = models.CharField(max_length=254, null=True)

    class Meta:
        ordering = ['module']

    def __str__(self) -> str:
        return self.name

    @property
    def name(self) -> str:
        return self.label or self.module


class MetricModel(models.Model):
    created_at = models.DateTimeField(db_index=True, default=timezone.now)
    label = models.CharField(max_length=254)

    question = models.TextField(blank=True, null=True)
    desc = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True


class Counter(MetricModel):
    """Counter value, the label is unique per app"""

    value = models.BigIntegerField(default=0)
    trend = models.JSONField(default=list, blank=True)
    app = models.ForeignKey(App, related_name='counters', on_delete=models.CASCADE)

    class Meta:
        app_label = database_entry
        ordering = ['pk']
        constraints = [
            models.UniqueConstraint(
                fields=['app', 'label'], name='counter_unique_app_label'
            )
        ]

    def __str__(self) -> str:
        return f"Insight Counter: {self.label} = {self.value}"


class Gauge(MetricModel):
    """Gauge value, the label is unique per app"""

    value = models.FloatField(default=0.0)
    trend = models.JSONField(default=list, blank=True)
    app = models.ForeignKey(App, related_name='gauges', on_delete=models.CASCADE)

    class Meta:
        app_label = database_entry
        ordering = ['pk']
        constraints = [
            models.UniqueConstraint(
                fields=['app', 'label'], name='gauge_unique_app_label'
            )
        ]

    def __str__(self) -> str:
        return f"Insight Gauge: {self.label} = {self.value}"


class Bucket(MetricModel):
    app = models.ForeignKey(App, related_name='buckets', on_delete=models.CASCADE)

    type = models.IntegerField(
        choices=BucketType.BUCKET_TYPES, default=BucketType.TIMESERIES
    )

    # Bucket specific plot options
    xlabel = models.CharField(max_length=254, blank=True, null=True)
    xformat = models.CharField(max_length=254, blank=True, null=True)
    ylabel = models.CharField(max_length=254, blank=True, null=True)
    yformat = models.CharField(max_length=254, blank=True, null=True)

    # title for plot
    title = models.CharField(max_length=254, blank=True, null=True)

    objects = BucketManager()

    class Meta:
        app_label = database_entry
        ordering = ['pk']
        constraints = [
            models.UniqueConstraint(
                fields=['app', 'label'], name='bucket_unique_app_label'
            )
        ]

    def __str__(self) -> str:
        return f"Insight Bucket: {self.label}"

    @property
    def is_timeseries(self) -> bool:
        return self.type == BucketType.TIMESERIES

    @property
    def is_scatterplot(self) -> bool:
        return self.type == BucketType.SCATTERPLOT

    @property
    def is_barchart(self) -> bool:
        return self.type == BucketType.BARCHART

    @property
    def is_hbarchart(self) -> bool:
        return self.type == BucketType.HBARCHART


class BucketValue(models.Model):
    """Bucket values matrix, used by every chart type"""

    # Timestamp for timeseries
    timestamp = models.DateTimeField(db_index=True, blank=True, null=True)

    # Matrix
    xvalue = models.FloatField(default=0.0)
    yvalue = models.FloatField(default=0.0)
    category = models.CharField(db_index=True, max_length=254, null=True)

    bucket = models.ForeignKey(Bucket, related_name='values', on_delete=models.CASCADE)

    class Meta:
        app_label = database_entry
        ordering = ['timestamp', 'pk']
        constraints = [
            models.UniqueConstraint(
                fields=['bucket', 'timestamp'],
                name='bucketvalue_unique_bucket_timestamp',
            )
        ]

    def __str__(self) -> str:
        return (
            "Insight Bucket value: "
            f" timestamp={self.bucket.label}.{self.timestamp} x={self.xvalue} y={self.yvalue}"
        )
