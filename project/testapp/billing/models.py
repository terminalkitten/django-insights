from django.db import models


class Subscription(models.Model):
    class Plan(models.TextChoices):
        FREE = 'free'
        TEAM = 'team'
        BUSINESS = 'business'

    workspace = models.ForeignKey(
        'testapp.Workspace', related_name='subscriptions', on_delete=models.CASCADE
    )
    plan = models.CharField(max_length=8, choices=Plan.choices)
    seats = models.PositiveIntegerField()
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)


class Invoice(models.Model):
    class Status(models.TextChoices):
        PAID = 'paid'
        OPEN = 'open'
        OVERDUE = 'overdue'

    subscription = models.ForeignKey(
        Subscription, related_name='invoices', on_delete=models.CASCADE
    )
    issued_at = models.DateTimeField(db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=8, choices=Status.choices)
