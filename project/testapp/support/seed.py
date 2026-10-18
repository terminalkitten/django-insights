from __future__ import annotations

import random
from datetime import datetime, timedelta

from project.testapp.models import Membership, Workspace
from project.testapp.moments import random_moment
from project.testapp.support.models import Ticket

CHANNEL_WEIGHTS = {'email': 0.5, 'chat': 0.38, 'phone': 0.12}
PRIORITY_WEIGHTS = {'low': 0.35, 'normal': 0.5, 'urgent': 0.15}
RESPONSE_HOURS = {'low': 5.0, 'normal': 2.5, 'urgent': 0.5}
RESOLUTION_HOURS = {'low': 60.0, 'normal': 30.0, 'urgent': 8.0}


def seed_support(
    rng: random.Random,
    total: int,
    workspaces: list[Workspace],
    memberships: list[Membership],
    end: datetime,
) -> None:
    """Urgent tickets get answered quicker, fast resolutions leave happier customers"""
    Ticket.objects.all().delete()

    by_workspace: dict[int, list[Membership]] = {w.pk: [] for w in workspaces}
    for membership in memberships:
        by_workspace[membership.workspace.pk].append(membership)

    channels = list(CHANNEL_WEIGHTS)
    priorities = list(PRIORITY_WEIGHTS)
    weights = [len(workspaces) - number for number in range(len(workspaces))]
    tickets = []
    for workspace in rng.choices(workspaces, weights, k=total):
        members = by_workspace[workspace.pk]
        if not members:
            continue
        membership = rng.choice(members)
        created_at = random_moment(rng, membership.joined_at, end)
        priority = rng.choices(priorities, list(PRIORITY_WEIGHTS.values()))[0]

        first_response = created_at + timedelta(
            hours=rng.lognormvariate(0, 0.9) * RESPONSE_HOURS[priority]
        )
        hours = rng.lognormvariate(0, 0.8) * RESOLUTION_HOURS[priority]
        resolved_at = created_at + timedelta(hours=hours)
        resolved = resolved_at < end and rng.random() < 0.96

        satisfaction = None
        if resolved and rng.random() < 0.6:
            quick = hours < RESOLUTION_HOURS[priority]
            satisfaction = rng.choices(
                [1, 2, 3, 4, 5], [1, 2, 4, 9, 14] if quick else [4, 5, 6, 5, 3]
            )[0]

        tickets.append(
            Ticket(
                workspace=workspace,
                requester=membership.user,
                channel=rng.choices(channels, list(CHANNEL_WEIGHTS.values()))[0],
                priority=priority,
                created_at=created_at,
                first_response_at=first_response if first_response < end else None,
                resolved_at=resolved_at if resolved else None,
                satisfaction=satisfaction,
            )
        )
    Ticket.objects.bulk_create(tickets, batch_size=2000)
