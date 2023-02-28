from random import choice, randrange

from django.core.management.base import BaseCommand
from faker import Faker

from project.testapp.models import Author, Book

fake = Faker()


class Command(BaseCommand):

    """Seed TestApp database"""

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('[TestApp] - Database seed'))

        Author.objects.all().delete()
        Book.objects.all().delete()

        authors = []
        books = []

        names = [fake.unique.name() for i in range(2000)]
        titles = [fake.sentence(nb_words=randrange(30)) for i in range(245)]

        for name in names:
            authors.append(Author(name=name, age=randrange(80)))

        for title in titles:
            books.append(Book(author=choice(authors), title=title))

        Author.objects.bulk_create(authors)
        Book.objects.bulk_create(books)
