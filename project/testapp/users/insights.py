from __future__ import annotations

from django_insights.metrics import metrics
from project.testapp.users.models import AppUser

label = "Users"


@metrics.counter(
    question="How many app users we have in our store?",
    desc="Number of app users",
)
def count_app_users() -> int:
    return AppUser.objects.count()
