from typing import Self

from django.db import models

from django_insights.choices import BucketType


class BucketQuerySet(models.QuerySet):
    def of_type(self, bucket_type: int) -> Self:
        """Buckets of one type, with their values loaded in a single extra query"""
        return self.filter(type=bucket_type).prefetch_related('values')

    def timeseries(self) -> Self:
        return self.of_type(BucketType.TIMESERIES)

    def scatterplots(self) -> Self:
        return self.of_type(BucketType.SCATTERPLOT)

    def barcharts(self) -> Self:
        return self.of_type(BucketType.BARCHART)

    def hbarcharts(self) -> Self:
        return self.of_type(BucketType.HBARCHART)


class BucketManager(models.Manager):
    def get_queryset(self) -> BucketQuerySet:
        return BucketQuerySet(self.model, using=self._db)

    def timeseries(self) -> BucketQuerySet:
        return self.get_queryset().timeseries()

    def scatterplots(self) -> BucketQuerySet:
        return self.get_queryset().scatterplots()

    def barcharts(self) -> BucketQuerySet:
        return self.get_queryset().barcharts()

    def hbarcharts(self) -> BucketQuerySet:
        return self.get_queryset().hbarcharts()
