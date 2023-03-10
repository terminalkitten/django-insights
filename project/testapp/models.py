from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone


class AppUser(AbstractBaseUser, PermissionsMixin):
    created = models.DateTimeField('created')
    modified = models.DateTimeField('modified', auto_now=True)

    email = models.EmailField(blank=True, default="", unique=True)
    last_login = models.DateTimeField(blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []


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
