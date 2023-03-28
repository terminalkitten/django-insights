from random import choice, randrange

from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from project.testapp.models import Author, Book
from project.testapp.users.models import AppUser

fake = Faker()


class Command(BaseCommand):

    """Seed TestApp database"""

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('[TestApp] - Database seed'))

        AppUser.objects.create(email="user@example.com")

        Author.objects.all().delete()
        Book.objects.all().delete()

        authors = []

        names = [fake.unique.name() for i in range(2000)]
        titles = [fake.sentence(nb_words=randrange(30)) for i in range(5000)]

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
