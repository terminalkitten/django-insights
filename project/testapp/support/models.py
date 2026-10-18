from django.conf import settings
from django.db import models


class Ticket(models.Model):
    class Channel(models.TextChoices):
        EMAIL = 'email'
        CHAT = 'chat'
        PHONE = 'phone'

    class Priority(models.TextChoices):
        LOW = 'low'
        NORMAL = 'normal'
        URGENT = 'urgent'

    workspace = models.ForeignKey(
        'testapp.Workspace', related_name='tickets', on_delete=models.CASCADE
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name='tickets',
        on_delete=models.SET_NULL,
    )
    channel = models.CharField(max_length=8, choices=Channel.choices)
    priority = models.CharField(
        max_length=8, choices=Priority.choices, default=Priority.NORMAL
    )
    created_at = models.DateTimeField(db_index=True)
    first_response_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    satisfaction = models.PositiveSmallIntegerField(null=True, blank=True)
