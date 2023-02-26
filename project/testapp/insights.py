from django_insights.metrics import CounterType, InsightMetrics
from project.testapp.models import Author

metrics = InsightMetrics()


@metrics.counter(question="How many authors are there?")
def count_authors() -> CounterType:
    num_of_authors = Author.objects.count()
    return CounterType(value=num_of_authors)
