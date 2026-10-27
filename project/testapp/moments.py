from __future__ import annotations

import random
from datetime import datetime, timedelta

WEEKDAY_WEIGHTS = [0.9, 1.0, 1.0, 1.0, 0.7, 0.06, 0.04]
HOUR_WEIGHTS = [0.02] * 7 + [1, 3, 4, 4, 3, 2, 3, 4, 4, 3, 2, 1] + [0.2] * 5


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
