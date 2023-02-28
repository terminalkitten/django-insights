from datetime import datetime

from django.db.models import Avg, Count
from django.db.models.functions import TruncMonth, TruncYear

from django_insights.metrics import metrics
from project.testapp.models import Author, Book


@metrics.counter(question="How many authors are there?")
def count_authors() -> int:
    return Author.objects.count()


@metrics.counter(question="How many books are there?")
def count_books() -> int:
    return Book.objects.count()


@metrics.counter(question="Authors with two or more books?")
def count_authors_with_two_or_more_books() -> int:
    return (
        Author.objects.prefetch_related('books')
        .annotate(total_books=Count('books'))
        .filter(total_books__gte=2)
        .count()
    )


@metrics.counter(question="Authors without books?")
def count_authors_without_books() -> int:
    return (
        Author.objects.prefetch_related('books')
        .annotate(total_books=Count('books'))
        .filter(total_books=0)
        .count()
    )


@metrics.gauge(question="Average book(s) per author?")
def avg_books_per_author() -> int:
    avg_total_books = (
        Author.objects.prefetch_related('books')
        .annotate(total_books=Count('books'))
        .aggregate(Avg('total_books'))
        .get('total_books__avg')
    )

    return round(avg_total_books, 2)


@metrics.timeseries(
    question="Num of books created per month?",
    xlabel="Month",
    xformat='%m',
    ylabel="Num of books",
)
def num_of_books_per_month() -> list[tuple[datetime, int]]:
    return (
        Book.objects.all()
        .annotate(month=TruncMonth('created'))
        .values('month')
        .filter(month__isnull=False)
        .annotate(total=Count('pk'))
        .values_list('month', 'total')
        .order_by('month')
    )


@metrics.timeseries(
    question="Num of books created per year?",
    xlabel="Year",
    xformat='%Y',
    ylabel="Num of books",
)
def num_of_books_per_year() -> list[tuple[datetime, int]]:
    return (
        Book.objects.all()
        .annotate(year=TruncYear('created'))
        .values('year')
        .filter(year__isnull=False)
        .annotate(total=Count('pk'))
        .values_list('year', 'total')
        .order_by('year')
    )
