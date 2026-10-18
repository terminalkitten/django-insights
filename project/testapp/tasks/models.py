from django.conf import settings
from django.db import models


class Project(models.Model):
    workspace = models.ForeignKey(
        'testapp.Workspace', related_name='projects', on_delete=models.CASCADE
    )
    name = models.CharField(max_length=64)
    created_at = models.DateTimeField()


class Task(models.Model):
    class Priority(models.TextChoices):
        LOW = 'low'
        MEDIUM = 'medium'
        HIGH = 'high'

    project = models.ForeignKey(Project, related_name='tasks', on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name='created_tasks',
        on_delete=models.SET_NULL,
    )
    priority = models.CharField(
        max_length=8, choices=Priority.choices, default=Priority.MEDIUM
    )
    created_at = models.DateTimeField(db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
