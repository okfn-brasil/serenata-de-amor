from django.contrib.postgres.fields import ArrayField
from django.db import models
from jsonfield import JSONField
from uuid import uuid4

from django_bulk_update.manager import BulkUpdateManager


class Role(models.Model):
    code = models.IntegerField()


class Person(models.Model):
    """
        test model
    """
    role = models.ForeignKey(Role, null=True)
    big_age = models.BigIntegerField()
    comma_separated_age = models.CommaSeparatedIntegerField(max_length=255)
    age = models.IntegerField()
    positive_age = models.PositiveIntegerField()
    positive_small_age = models.PositiveSmallIntegerField()
    small_age = models.SmallIntegerField()
    height = models.DecimalField(max_digits=3, decimal_places=2)
    float_height = models.FloatField()

    certified = models.BooleanField(default=False)
    null_certified = models.NullBooleanField()

    name = models.CharField(max_length=140, blank=True, null=True)
    email = models.EmailField()
    file_path = models.FilePathField()
    slug = models.SlugField()
    text = models.TextField()
    url = models.URLField()

    date_time = models.DateTimeField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)

    remote_addr = models.GenericIPAddressField(null=True, blank=True)

    my_file = models.FileField(upload_to='/some/path/', null=True, blank=True)
    image = models.ImageField(upload_to='/some/path/', null=True, blank=True)

    data = JSONField(null=True, blank=True)

    default = models.IntegerField(null=True, blank=True,
                                  help_text="A reserved keyword")

    jobs = models.ManyToManyField(
        'Company', blank=True, related_name='workers')

    objects = BulkUpdateManager()


class Company(models.Model):
    name = models.CharField(max_length=50)
    president = models.ForeignKey(Person, related_name='companies')


class PersonUUID(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid4)
    age = models.IntegerField()

    objects = BulkUpdateManager()


class Brand(models.Model):
    name = models.CharField(max_length=128, unique=True, db_index=True)
    codes = ArrayField(models.CharField(max_length=64), default=['code_1'])

    objects = BulkUpdateManager()
