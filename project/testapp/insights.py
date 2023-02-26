from django_insights.metrics import InsightMetrics
from project.testapp.models import Author

metrics = InsightMetrics()


@metrics.counter(question="How many authors are there?")
def count_authors() -> int:
    return Author.objects.count()
