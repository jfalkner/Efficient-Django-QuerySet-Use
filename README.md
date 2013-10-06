Efficient Django QuerySet Use
=============================

Code and slides from [Jayson Falkner's](http://bitapocalypse.com/jayson/about/2013/07/17/jayson-falkner/) "Efficient Django QuerySet Use".

### Counsyl.objects.filter(django_queryset_type=EXAMPLES, helpful=True)<br/>(Helpful examples of Django QuerySet use at Counsyl)

This talk is about advanced use of Django's QuerySet API based on lessons learned at Counsyl. You'll learn how to debug, optimize and use the QuerySet API efficiently. The main examples focus on demystifying how QuerySet maps to SQL and how seemingly simple Python code, presumably fast O(1) queries, can result in unacceptably long runtime and often O(N) or worse queries. Solutions are provided for keeping your Python code simple and RDMS use performant.

### Speaker Bio:

Jayson Falker is a software developer for Counsyl. He has an EEN/CS degree and a PhD in Bioinformatics. He is a long-time open-source Linux/Java/Web developer, book author, and presenter. He has focused on proteomics and genomics research since the mid-2000's, including working for a few years at startups and for Dow AgroSciences. Jayson is quick to get his geek on and also loves to build ridiculous side-projects, including a 6' tall Jenga set that weighs 300lbs and mobile apps that give you awesome virtual mustaches.

### Presentations

This material comes from work experience at Counsyl and has been presented at the following events:

- Oct 10th, 2013 - [The San Francisco Django Meetup Group](http://www.meetup.com/The-San-Francisco-Django-Meetup-Group/events/141505312/) @ [Counsyl](http://maps.google.com/maps?q=180+Kimball+Way%2C+South+San+Francisco%2C+CA)
- Nov 12th 2013 - [Portland Python Users Group](http://www.meetup.com/pdxpython/events/139924722/) @ [Urban Airship](http://maps.google.com/maps?q=1417+NW+Everett+St%2C+Portland%2C+OR)

If you think this talk would be good for your user group or conference, contact jayson@counsyl.com.

### Reuse

You are encouraged to take this material and reuse it according to the included [MIT license](LICENSE). In short, you can use it however you like but the work is provided AS IS and you need to include the license to recognize the original authors and Counsyl.


### Examples

Below are the scripts to run the examples from the slides. All scripts assume:

- You are running Python 2.7.2 (newer versions may work fine too)
- You have Django 1.5 installed
- You are in the base directory. The one with this file.

#### Example Set #1: Query With Loop, prefetch_related(), select_related()

This set includes doing the often intuitive yet worst possible QuerySet use. Optimization methods of using `select_related()` and `prefetch_related()` demonstrated a 10x speed increase.

```
# Setup the demo's data models.
cd demo
python manage.py reset example
python manage.py syncdb

# Run the demo.
python manage.py shell


# Make the fake data.
from example.utils import make_fake_data
make_fake_data()

# Run the query.
from example.models import Sample, SampleStatus
import counsyl.db
from django.db.models import Max


# Run the worst performance, looping query.
%cpaste
counsyl.db.track_sql()
results = []
samples = Sample.objects.filter(
    production=True,
    statuses__status_code=SampleStatus.LAB)
for sample in samples:
    results.append((sample.barcode, sample.status().created))
counsyl.db.print_sql()
counsyl.db.print_sql(show_queries=False)
--


# Run the prefetch_related(), looping query.
%cpaste
counsyl.db.track_sql()
results = []
samples = Sample.objects.filter(
    production=True,
    statuses__status_code=SampleStatus.LAB)
samples = samples.prefetch_related('statuses')
for sample in samples:
    results.append((sample.barcode, sample.status().created))
counsyl.db.print_sql()
counsyl.db.print_sql(show_queries=False)
--


# Run the select_related(), looping query.
%cpaste
counsyl.db.track_sql()
results = []
samples = Sample.objects.filter(
    production=True,
    statuses__status_code=SampleStatus.LAB)
samples = samples.select_related('latest_status')
for sample in samples:
    results.append((sample.barcode, sample.latest_status.created))
counsyl.db.print_sql()
--
```

#### Example #2: Denormalization and Multi-column INDEX

This set includes the optimal known solution for using Postgres including denormalizing the fields used for the query and a multicolumn index.


```
# Reset the data models and load a denormalized view.
cd demo-optimized
python manage.py reset example
python manage.py syncdb


# Launch the shell.
python manage.py shell

# Make up 1,000,000 fake samples. Won't take long.
from example.utils import make_fake_data
make_fake_data(samples_to_make=1000000)


# Query without a multicolumn index.
%cpaste
counsyl.db.track_sql()
vals = list(Sample.objects
                  .filter(production=True,
                          status_code = SampleStatus.LAB)
                  .values_list('barcode', 'status_changed'))
counsyl.db.print_sql()
--


# Create the multicolumn index.
from counsyl.db import pg_multicolumn_index
pg_multicolumn_index(Sample, ['production', 'status_code'])


# Re-do the same query above but this time the index is available.
 %cpaste
counsyl.db.track_sql()
vals = list(Sample.objects
                  .filter(production=True,
                          status_code = SampleStatus.LAB)
                  .values_list('barcode', 'status_changed'))
counsyl.db.print_sql()
--


# Make 100,000,000 rows. This takes awhile!
from example.utils import make_fake_data
make_fake_data(samples_to_make=100000000, batch_threshold=1000000, make_statuses=False)


# Optimal query including multicolumn index. 100,000,000 in sub second!
%cpaste
counsyl.db.track_sql()
vals = list(Sample.objects
                  .filter(production=True,
                          status_code = SampleStatus.LAB)
                  .values_list('barcode', 'status_changed'))
counsyl.db.print_sql()
--
```


