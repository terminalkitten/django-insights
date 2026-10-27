from __future__ import annotations

import random
from datetime import datetime, timedelta
from decimal import Decimal

from project.testapp.billing.models import Invoice, Subscription
from project.testapp.models import Membership, Workspace

PRICE_PER_SEAT = {
    Subscription.Plan.FREE: Decimal('0'),
    Subscription.Plan.TEAM: Decimal('8'),
    Subscription.Plan.BUSINESS: Decimal('15'),
}


def seed_billing(
    rng: random.Random, workspaces: list[Workspace], end: datetime
) -> None:
    """Workspaces start free, most upgrade over time and a few cancel"""
    Invoice.objects.all().delete()
    Subscription.objects.all().delete()

    seats = {
        workspace.pk: Membership.objects.filter(workspace=workspace).count()
        for workspace in workspaces
    }
    subscriptions = []
    for workspace in workspaces:
        plans = [Subscription.Plan.FREE]
        if rng.random() < 0.85:
            plans.append(Subscription.Plan.TEAM)
            if rng.random() < 0.5:
                plans.append(Subscription.Plan.BUSINESS)

        started = workspace.created_at
        for number, plan in enumerate(plans):
            last = number == len(plans) - 1
            ended = None
            if not last:
                ended = started + timedelta(days=rng.randrange(45, 300))
            elif plan != Subscription.Plan.FREE and rng.random() < 0.15:
                ended = started + timedelta(days=rng.randrange(60, 400))
            if ended and ended >= end:
                ended = None if last else end - timedelta(days=1)
            subscriptions.append(
                Subscription(
                    workspace=workspace,
                    plan=plan,
                    seats=seats[workspace.pk],
                    monthly_price=PRICE_PER_SEAT[plan] * seats[workspace.pk],
                    started_at=started,
                    ended_at=ended,
                )
            )
            if ended is None:
                break
            started = ended
    Subscription.objects.bulk_create(subscriptions)

    invoices = []
    for subscription in Subscription.objects.all():
        if not subscription.monthly_price:
            continue
        issued = subscription.started_at
        stop = subscription.ended_at or end
        while issued < stop:
            recent = end - issued < timedelta(days=30)
            status = Invoice.Status.OPEN if recent else Invoice.Status.PAID
            if not recent and rng.random() < 0.05:
                status = Invoice.Status.OVERDUE
            invoices.append(
                Invoice(
                    subscription=subscription,
                    issued_at=issued,
                    amount=subscription.monthly_price,
                    status=status,
                )
            )
            issued += timedelta(days=30)
    Invoice.objects.bulk_create(invoices, batch_size=2000)
