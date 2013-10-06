from django.db import models


class Sample(models.Model):
    barcode = models.CharField(max_length=10, unique=True)
    production = models.BooleanField()
    created = models.DateTimeField()
    status_code = models.PositiveSmallIntegerField()
    status_created = models.DateTimeField()


class SampleStatus(models.Model):
    sample = models.ForeignKey(Sample, related_name='statuses')
    status_code = models.PositiveSmallIntegerField()
    created = models.DateTimeField()

    RECEIVED = 1
    LAB = 2
    COMPLETE = 3
    ERROR = 4
