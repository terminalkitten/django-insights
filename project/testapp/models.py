from django.conf import settings
from django.db import models


class Workspace(models.Model):
    name = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField()
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through='Membership', related_name='workspaces'
    )


class Membership(models.Model):
    class Role(models.TextChoices):
        OWNER = 'owner'
        ADMIN = 'admin'
        MEMBER = 'member'

    workspace = models.ForeignKey(
        Workspace, related_name='memberships', on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='memberships', on_delete=models.CASCADE
    )
    role = models.CharField(max_length=8, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['workspace', 'user'], name='membership_unique_workspace_user'
            )
        ]


class Channel(models.Model):
    workspace = models.ForeignKey(
        Workspace, related_name='channels', on_delete=models.CASCADE
    )
    name = models.CharField(max_length=32)
    created_at = models.DateTimeField()
    is_private = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['workspace', 'name'], name='channel_unique_workspace_name'
            )
        ]


class Message(models.Model):
    channel = models.ForeignKey(
        Channel, related_name='messages', on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name='messages',
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(db_index=True)
    is_ai = models.BooleanField(default=False)
    model = models.CharField(max_length=32, blank=True, default='')
    tokens = models.PositiveIntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)


class Report(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft'
        READY = 'ready'
        FAILED = 'failed'

    workspace = models.ForeignKey(
        Workspace, related_name='reports', on_delete=models.CASCADE
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='reports', on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(db_index=True)
    status = models.CharField(
        max_length=8, choices=Status.choices, default=Status.DRAFT
    )
