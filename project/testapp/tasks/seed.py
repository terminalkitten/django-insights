from __future__ import annotations

import random
from datetime import datetime, timedelta

from project.testapp.models import Membership, Workspace
from project.testapp.tasks.models import Project, Task

PROJECTS = ['Website', 'Mobile app', 'Onboarding', 'Billing', 'Migration', 'Research']
PRIORITIES = {'low': 0.3, 'medium': 0.5, 'high': 0.2}


def seed_tasks(
    rng: random.Random,
    total: int,
    workspaces: list[Workspace],
    memberships: list[Membership],
    end: datetime,
) -> None:
    """Most tasks get done, high priority ones faster, recent ones are still open"""
    Task.objects.all().delete()
    Project.objects.all().delete()

    projects = Project.objects.bulk_create(
        Project(
            workspace=workspace,
            name=name,
            created_at=workspace.created_at + timedelta(days=rng.randrange(120)),
        )
        for workspace in workspaces
        for name in rng.sample(PROJECTS, rng.randrange(2, len(PROJECTS) + 1))
    )

    by_workspace: dict[int, list[Membership]] = {w.pk: [] for w in workspaces}
    for membership in memberships:
        by_workspace[membership.workspace.pk].append(membership)

    priorities = list(PRIORITIES)
    weights = [len(projects) - number for number in range(len(projects))]
    tasks = []
    for project in rng.choices(projects, weights, k=total):
        members = by_workspace[project.workspace.pk]
        if not members:
            continue
        membership = rng.choice(members)
        start = max(membership.joined_at, project.created_at)
        if start >= end:
            continue
        created_at = start + (end - start) * rng.random() ** 0.7
        priority = rng.choices(priorities, list(PRIORITIES.values()))[0]
        days = rng.lognormvariate(1.6 if priority == 'high' else 2.4, 0.8)
        completed_at = created_at + timedelta(days=days)
        tasks.append(
            Task(
                project=project,
                created_by=membership.user,
                priority=priority,
                created_at=created_at,
                completed_at=completed_at if completed_at < end else None,
            )
        )
    Task.objects.bulk_create(tasks, batch_size=2000)
