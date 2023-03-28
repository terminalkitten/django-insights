from __future__ import annotations

from datetime import datetime
from typing import Any

from django.db.models import Avg, Case, Count, Value, When
from django.db.models.functions import Length, TruncMonth, TruncYear

from django_insights.metrics import metrics
from project.testapp.models import Author, Book

label = "Books"


@metrics.counter(
    question="How many authors are there in our store?",
    desc="Number of authors we sell books for in our store",
)
def count_authors() -> int:
    return Author.objects.count()


@metrics.counter(question="How many books are there?")
def count_books() -> int:
    return Book.objects.count()


@metrics.counter(question="Books with title longer than 20 chars?")
def count_books_title_gt_20() -> int:
    return (
        Book.objects.annotate(title_len=Length('title'))
        .filter(title_len__gt=20)
        .count()
    )


@metrics.counter(question="Books with title less than 10 chars?")
def count_books_title_lt_10() -> int:
    return (
        Book.objects.annotate(title_len=Length('title'))
        .filter(title_len__lt=10)
        .count()
    )


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


@metrics.counter(question="Authors with name longer than 20 chars?")
def count_authors_name_gt_20() -> int:
    return (
        Author.objects.annotate(name_len=Length('name')).filter(name_len__gt=20).count()
    )


@metrics.gauge(question="Average book(s) per author?")
def avg_books_per_author() -> int:
    avg_total_books = (
        Author.objects.prefetch_related('books')
        .annotate(total_books=Count('books'))
        .aggregate(Avg('total_books'))
        .get('total_books__avg')
    )

    return avg_total_books


@metrics.timeseries(
    question="Num of books created per month?",
    desc="How many books are added each month, since the opening of our store",
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


@metrics.scatterplot(
    question="Num of books by age of author?",
    xlabel="Age",
    ylabel="Num of books",
)
def author_age_vs_num_of_books() -> list[tuple[float, float, Any]]:
    return (
        Author.objects.values('age')
        .annotate(num_of_books=Count('books'), category=Value("author"))
        .values_list('num_of_books', 'age', 'category')
    )


@metrics.barchart(
    question="Num of books by gender of author?",
    xlabel="Gender",
    ylabel="Num of books",
)
def author_gender_vs_num_of_books() -> list[tuple[float, float, str]]:
    return (
        Author.objects.values('gender')
        .annotate(
            num_of_books=Count('books'),
            gender_category=Case(
                When(gender=1, then=Value('Male')),
                When(gender=2, then=Value('Female')),
            ),
        )
        .values_list('num_of_books', 'gender', 'gender_category')
    )
