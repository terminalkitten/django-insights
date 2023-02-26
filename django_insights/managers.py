from django.db import models

from django_insights.choices import BucketType


class BucketQuerySet(models.QuerySet):
    def timeseries(self):
        return self.filter(type=BucketType.TIMESERIES)

    def histograms(self):
        return self.filter(type=BucketType.HISTOGRAM)

    def scatterplots(self):
        return self.filter(type=BucketType.SCATTERPLOT)


class BucketManager(models.Manager):
    def get_queryset(self):
        return BucketQuerySet(self.model, using=self._db)

    def timeseries(self):
        return self.get_queryset().timeseries()

    def histograms(self):
        return self.get_queryset().histograms()

    def scatterplots(self):
        return self.get_queryset().scatterplots()
