from random import choice, randrange

from django.core.management.base import BaseCommand
from faker import Faker

from project.testapp.models import Author, Book

fake = Faker()


class Command(BaseCommand):

    """Seed TestApp database"""

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('[TestApp] - Database seed'))

        authors = []
        books = []

        names = [fake.name() for i in range(100)]

        for name in names:
            authors.append(Author(name=name, age=randrange(80)))
            books.append(Book(author=choice(authors), title=fake.sentence(nb_words=10)))

        Author.objects.bulk_create(authors)
        Book.objects.bulk_create(books)
