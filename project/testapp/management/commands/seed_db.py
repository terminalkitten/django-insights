from argparse import ArgumentParser
from random import choice, randrange
from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from project.testapp.models import Author, Book
from project.testapp.users.models import AppUser

fake = Faker()


class Command(BaseCommand):
    """Seed TestApp database"""

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument('--authors', type=int, default=2000)
        parser.add_argument('--books', type=int, default=5000)

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(self.style.HTTP_INFO('[TestApp] - Database seed'))
        fake.unique.clear()

        AppUser.objects.get_or_create(email="user@example.com")

        Author.objects.all().delete()
        Book.objects.all().delete()

        authors = []

        names = [fake.unique.name() for _ in range(options['authors'])]
        titles = [
            fake.sentence(nb_words=randrange(30)) for _ in range(options['books'])
        ]

        for name in names:
            author_created = fake.date_time_between_dates(
                datetime_start='-10y',
                datetime_end='now',
                tzinfo=timezone.get_current_timezone(),
            )
            authors.append(
                Author.objects.create(
                    created=author_created,
                    name=name,
                    age=randrange(80),
                    gender=fake.random.choice((1, 2)),
                )
            )

        for title in titles:
            book_created = fake.date_time_between_dates(
                datetime_start='-10y',
                datetime_end='now',
                tzinfo=timezone.get_current_timezone(),
            )

            Book.objects.create(
                created=book_created, author=choice(authors), title=title
            )
