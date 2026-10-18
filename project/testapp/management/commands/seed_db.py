from __future__ import annotations

import random
from argparse import ArgumentParser
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from project.testapp.billing.seed import seed_billing
from project.testapp.models import Channel, Membership, Message, Report, Workspace
from project.testapp.tasks.seed import seed_tasks
from project.testapp.users.models import AppUser

WORKSPACES = [
    'Acme',
    'Globex',
    'Initech',
    'Umbrella',
    'Hooli',
    'Stark',
    'Wayne',
    'Wonka',
    'Cyberdyne',
    'Soylent',
    'Tyrell',
    'Vandelay',
]
CHANNELS = ['general', 'random', 'engineering', 'support', 'sales', 'design', 'ops']
AI_MODELS = {
    'assistant-small': Decimal('0.0000006'),
    'assistant-large': Decimal('0.000012'),
}
REPORT_STATUS_WEIGHTS = {'draft': 0.2, 'ready': 0.7, 'failed': 0.1}
WEEKDAY_WEIGHTS = [0.9, 1.0, 1.0, 1.0, 0.7, 0.06, 0.04]
HOUR_WEIGHTS = [0.02] * 7 + [1, 3, 4, 4, 3, 2, 3, 4, 4, 3, 2, 1] + [0.2] * 5
INVITED_SHARE = 0.4


def random_moment(rng: random.Random, start: datetime, end: datetime) -> datetime:
    """Busy on Tuesday to Thursday, quiet in the weekend and at night"""
    days = (end.date() - start.date()).days
    for _ in range(50):
        moment = (start + timedelta(days=rng.randint(0, days))).replace(
            hour=rng.choices(range(24), HOUR_WEIGHTS)[0],
            minute=rng.randrange(60),
            second=rng.randrange(60),
            microsecond=0,
        )
        if start <= moment <= end and rng.random() < WEEKDAY_WEIGHTS[moment.weekday()]:
            return moment
    return start + timedelta(seconds=rng.random() * (end - start).total_seconds())


class Command(BaseCommand):
    """Seed the demo with a team workspace and its AI assistant"""

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument('--users', type=int, default=600)
        parser.add_argument('--messages', type=int, default=30000)
        parser.add_argument('--years', type=int, default=3)
        parser.add_argument('--seed', type=int, default=42)

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(self.style.HTTP_INFO('[TestApp] - Database seed'))
        rng = random.Random(options['seed'])
        end = timezone.now().replace(microsecond=0)
        start = end - timedelta(days=365 * options['years'])

        self.reset()
        users = self.create_users(rng, options['users'], start, end)
        workspaces, members = self.create_workspaces(rng, users, start, end)
        channels = self.create_channels(rng, workspaces)
        self.create_messages(
            rng, options['messages'], users, members, channels, start, end
        )
        self.create_reports(rng, options['messages'] // 40, workspaces, members, end)
        seed_billing(rng, workspaces, end)
        seed_tasks(
            rng,
            options['messages'] // 5,
            workspaces,
            [membership for found in members.values() for membership in found],
            end,
        )

    def reset(self) -> None:
        Message.objects.all().delete()
        Report.objects.all().delete()
        Channel.objects.all().delete()
        Membership.objects.all().delete()
        Workspace.objects.all().delete()
        AppUser.objects.all().delete()

    def create_users(
        self, rng: random.Random, total: int, start: datetime, end: datetime
    ) -> list[AppUser]:
        """Signups grow over time, some users were invited by an earlier user"""
        span = (end - start).total_seconds()
        joined = sorted(
            start + timedelta(seconds=span * rng.random() ** 0.5) for _ in range(total)
        )
        AppUser.objects.bulk_create(
            AppUser(
                email=f'user{number:04d}@example.com',
                date_joined=moment,
                is_active=rng.random() > 0.03 + 0.25 * (end - moment) / (end - start),
            )
            for number, moment in enumerate(joined)
        )

        users = list(AppUser.objects.order_by('date_joined', 'pk'))
        for number, user in enumerate(users[1:], start=1):
            if rng.random() < INVITED_SHARE:
                user.invited_by = users[rng.randrange(number)]
        AppUser.objects.bulk_update(users, ['invited_by'])
        return users

    def create_workspaces(
        self,
        rng: random.Random,
        users: list[AppUser],
        start: datetime,
        end: datetime,
    ) -> tuple[list[Workspace], dict[int, list[Membership]]]:
        workspaces = Workspace.objects.bulk_create(
            Workspace(name=name, created_at=start + timedelta(days=rng.randrange(60)))
            for name in WORKSPACES
        )
        weights = [len(workspaces) - number for number in range(len(workspaces))]

        memberships = []
        for user in users:
            wanted = rng.choices([1, 2, 3], [0.6, 0.3, 0.1])[0]
            chosen: dict[int, Workspace] = {}
            while len(chosen) < min(wanted, len(workspaces)):
                workspace = rng.choices(workspaces, weights)[0]
                chosen[workspace.pk] = workspace
            for workspace in chosen.values():
                joined = max(user.date_joined, workspace.created_at) + timedelta(
                    hours=rng.randrange(72)
                )
                memberships.append(
                    Membership(
                        workspace=workspace,
                        user=user,
                        role=rng.choices(
                            ['owner', 'admin', 'member'], [0.02, 0.1, 0.88]
                        )[0],
                        joined_at=min(joined, end),
                    )
                )
        Membership.objects.bulk_create(memberships)

        members: dict[int, list[Membership]] = {user.pk: [] for user in users}
        for membership in memberships:
            members[membership.user.pk].append(membership)
        return workspaces, members

    def create_channels(
        self, rng: random.Random, workspaces: list[Workspace]
    ) -> dict[int, list[Channel]]:
        channels = [
            Channel(
                workspace=workspace,
                name=name,
                created_at=workspace.created_at + timedelta(days=rng.randrange(30)),
                is_private=rng.random() < 0.2,
            )
            for workspace in workspaces
            for name in rng.sample(CHANNELS, rng.randrange(4, len(CHANNELS) + 1))
        ]
        Channel.objects.bulk_create(channels)

        by_workspace: dict[int, list[Channel]] = {w.pk: [] for w in workspaces}
        for channel in Channel.objects.select_related('workspace').order_by('pk'):
            by_workspace[channel.workspace.pk].append(channel)
        return by_workspace

    def create_messages(
        self,
        rng: random.Random,
        total: int,
        users: list[AppUser],
        members: dict[int, list[Membership]],
        channels: dict[int, list[Channel]],
        start: datetime,
        end: datetime,
    ) -> None:
        """A few power users write most messages, the AI writes more of them over time"""
        span = (end - start).total_seconds()
        weights = [rng.paretovariate(1.16) for _ in users]
        models = list(AI_MODELS)

        messages = []
        for user in rng.choices(users, weights, k=total):
            membership = rng.choice(members[user.pk])
            options = channels[membership.workspace.pk]
            channel = rng.choices(
                options, [len(options) - n for n in range(len(options))]
            )[0]
            created_at = random_moment(
                rng, max(membership.joined_at, channel.created_at), end
            )

            progress = (created_at - start).total_seconds() / span
            message = Message(channel=channel, author=user, created_at=created_at)
            if rng.random() < 0.05 + 0.45 * progress:
                model = rng.choices(models, [0.75, 0.25])[0]
                message.author = None
                message.is_ai = True
                message.model = model
                message.tokens = max(40, int(rng.lognormvariate(6.0, 0.7)))
                message.cost = (message.tokens * AI_MODELS[model]).quantize(
                    Decimal('0.000001')
                )
            messages.append(message)

        Message.objects.bulk_create(messages, batch_size=2000)

    def create_reports(
        self,
        rng: random.Random,
        total: int,
        workspaces: list[Workspace],
        members: dict[int, list[Membership]],
        end: datetime,
    ) -> None:
        by_workspace: dict[int, list[Membership]] = {w.pk: [] for w in workspaces}
        for memberships in members.values():
            for membership in memberships:
                by_workspace[membership.workspace.pk].append(membership)

        statuses = list(REPORT_STATUS_WEIGHTS)
        weights = list(REPORT_STATUS_WEIGHTS.values())
        reports = []
        for workspace in rng.choices(workspaces, k=total):
            if not by_workspace[workspace.pk]:
                continue
            membership = rng.choice(by_workspace[workspace.pk])
            reports.append(
                Report(
                    workspace=workspace,
                    created_by=membership.user,
                    created_at=random_moment(rng, membership.joined_at, end),
                    status=rng.choices(statuses, weights)[0],
                )
            )
        Report.objects.bulk_create(reports)
