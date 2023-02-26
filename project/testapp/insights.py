from django_insights.metrics import metrics
from project.testapp.models import Author


@metrics.counter(question="How many authors are there?")
def count_authors() -> int:
    return Author.objects.count()
