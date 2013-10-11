from django.utils.timezone import utc

from django_db_utils import pg_bulk_update

from example.models import Sample, SampleStatus


def now():
    from datetime import datetime
    return datetime.utcnow().replace(tzinfo=utc)


def make_fake_data(samples_to_make=1000, batch_threshold=1000, delete_existing=True, make_statuses=True, years=1):
    """Makes mock data for testing performance. Optionally, resets db.
    """
    if delete_existing:
        Sample.objects.all().delete()
        print "Deleted existing"

    # Make up a set of
    offset = samples_to_make-samples_to_make/52/years

    # Create all the samples.
    samples = []
    for barcode in range(samples_to_make):
        sample = Sample()
        sample.barcode = str(barcode)
        sample.created = now()
        sample.production = True
        samples.append(sample)
        if len(samples) >= batch_threshold:
            Sample.objects.bulk_create(samples)
            del samples[:]
            print "Made %s samples."%Sample.objects.count()
    if samples:
        Sample.objects.bulk_create(samples)
    print "Finished making %s samples."%Sample.objects.count()

    if not make_statuses:
        return

    # Pull all ids for samples.
    sample_ids = Sample.objects.values_list('id', flat=True)

    # Create all the statuses.
    offset = len(sample_ids)-len(sample_ids)/52/years
    statuses = []
    for sample in sample_ids[:offset]:
        statuses.append(SampleStatus(sample_id=sample, status_code=SampleStatus.RECEIVED, created=now()))
        statuses.append(SampleStatus(sample_id=sample, status_code=SampleStatus.LAB, created=now()))
        statuses.append(SampleStatus(sample_id=sample, status_code=SampleStatus.COMPLETE, created=now()))
        if len(statuses) >= batch_threshold:
            SampleStatus.objects.bulk_create(statuses)
            del statuses[:]
    for sample in sample_ids[offset:]:
        statuses.append(SampleStatus(sample_id=sample, status_code=SampleStatus.RECEIVED, created=now()))
        statuses.append(SampleStatus(sample_id=sample, status_code=SampleStatus.LAB, created=now()))
        if len(statuses) >= batch_threshold:
            SampleStatus.objects.bulk_create(statuses)
            del statuses[:]
            print "Made %s statuses."%SampleStatus.objects.count()
    if statuses:
        SampleStatus.objects.bulk_create(statuses)
    print "Finished making %s statuses."%SampleStatus.objects.count()

    # Set all the statuses to lab.
    vals = (Sample.objects
            .filter(statuses__status_code=SampleStatus.LAB)
            .values_list('id', 'statuses__id'))
    sample_ids, sample_status_ids = zip(*vals)
    pg_bulk_update(Sample, 'id', 'latest_status', list(sample_ids), list(sample_status_ids))

    # Set all the statuses to completed.
    vals = (Sample.objects
            .filter(statuses__status_code=SampleStatus.COMPLETE)
            .values_list('id', 'statuses__id'))
    sample_ids, sample_status_ids = zip(*vals)
    pg_bulk_update(Sample, 'id', 'latest_status', list(sample_ids), list(sample_status_ids))
