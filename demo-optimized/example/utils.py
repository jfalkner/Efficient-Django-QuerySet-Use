from datetime import datetime
from django.utils.timezone import utc

from counsyl.db import pg_bulk_update

from example.models import Sample, SampleStatus


def now():
    from datetime import datetime
    return datetime.utcnow().replace(tzinfo=utc)


def make_fake_data(samples_to_make=100000, batch_threshold=100000, delete_existing=True, make_statuses=True, years=5):
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
        sample.status_created = sample.created
        if len(samples) < offset:
            sample.status_code = SampleStatus.COMPLETE
        else:
            sample.status_code = SampleStatus.LAB
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

    # Make all the denormalized status_code vars match.
    sync_status(limit=batch_threshold)
    print "Statuses synchronized"


def sync_status(limit=100000):
    # Stream through all samples.
    sample_count = Sample.objects.count()
    for index in range(0, sample_count, limit):
        vals = Sample.objects.order_by('id', '-statuses__status_code').distinct('id').values_list('id', 'status_code', 'statuses__id', 'statuses__status_code')[index:index+limit]
        # Pull all mismatching values.
        ids = []
        status_codes = []
#        status_ids = []
        for sample_id, status_code, status_id, latest_status_code in vals:
            if status_code != latest_status_code:
                ids.append(sample_id)
                status_codes.append(latest_status_code)
#                status_ids.append(status_id)
        # Sync using a bulk update.
        if ids:
            pg_bulk_update(Sample, 'id', 'status_code', list(ids), list(status_codes))
#            pg_bulk_update(Sample, 'id', 'status_id', list(ids), list(status_ids))
        print 'Synced %s out of %s samples at %s'%(len(ids), limit, index)
