from django.db import models


class Sample(models.Model):
    barcode = models.CharField(max_length=10, unique=True)
    production = models.BooleanField()
    created = models.DateTimeField()
    latest_status = models.ForeignKey('SampleStatus', related_name='+', null=True)

    def status(self):
        return self.statuses.all()[0]


class SampleStatus(models.Model):
    sample = models.ForeignKey(Sample, related_name='statuses')
    status = models.CharField(max_length=20)
    status_code = models.PositiveSmallIntegerField()
    created = models.DateTimeField()

    RECEIVED = 1
    LAB = 2
    COMPLETE = 3
    ERROR = 4
