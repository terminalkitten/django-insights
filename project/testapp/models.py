from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone


class AppUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(blank=True, default="", unique=True)
    last_login = models.DateTimeField(blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []


class Author(models.Model):
    created = models.DateTimeField('created', editable=False, auto_now_add=True)
    modified = models.DateTimeField('modified', auto_now=True)

    name = models.CharField(max_length=32, unique=True)
    age = models.IntegerField()


class Book(models.Model):
    created = models.DateTimeField('created', editable=False, auto_now_add=True)
    modified = models.DateTimeField('modified', auto_now=True)

    title = models.CharField(max_length=128)
    author = models.ForeignKey(Author, related_name='books', on_delete=models.CASCADE)
