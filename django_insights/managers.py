from django.db import models

from django_insights.choices import BucketType


class BucketQuerySet(models.QuerySet):
    def timeseries(self):
        return self.filter(type=BucketType.TIMESERIES)

    def histograms(self):
        return self.filter(type=BucketType.HISTOGRAM)

    def scatterplots(self):
        return self.filter(type=BucketType.SCATTERPLOT)

    def barcharts(self):
        return self.filter(type=BucketType.BARCHART)

    def hbarcharts(self):
        return self.filter(type=BucketType.HBARCHART)


class BucketManager(models.Manager):
    def get_queryset(self):
        return BucketQuerySet(self.model, using=self._db)

    def timeseries(self):
        return self.get_queryset().timeseries()

    def histograms(self):
        return self.get_queryset().histograms()

    def scatterplots(self):
        return self.get_queryset().scatterplots()

    def barcharts(self):
        return self.get_queryset().barcharts()

    def hbarcharts(self):
        return self.get_queryset().hbarcharts()
