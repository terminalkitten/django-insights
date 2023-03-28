from django.db import models


class Author(models.Model):
    created = models.DateTimeField('created')
    modified = models.DateTimeField('modified', auto_now=True)

    gender = models.IntegerField(choices=(('M', 1), ('F', 2)))
    name = models.CharField(max_length=32, unique=True)
    age = models.IntegerField()


class Book(models.Model):
    created = models.DateTimeField('created')
    modified = models.DateTimeField('modified', auto_now=True)

    title = models.CharField(max_length=128)
    author = models.ForeignKey(Author, related_name='books', on_delete=models.CASCADE)
