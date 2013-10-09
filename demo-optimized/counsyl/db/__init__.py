from datetime import datetime
from django.db import connection as con
import sqlparse


def track_sql():
    global start_time
    global query_count
    start_time = datetime.now()
    query_count = len(con.queries)

def print_sql(show_queries=True):
    print "Total Run Time: %s"%(datetime.now()-start_time)
    print "Total Postgres Time: %s"%sum([float(query['time']) for query in con.queries[query_count:]])
    print "Queries: %s"%(len(con.queries)-query_count)

    if show_queries:
        for query in con.queries[query_count:]:
            print "\nPostgres Time: %s"%query['time']
            print sqlparse.format(query['sql'], reindent=True, keyword_case='upper')


def pg_multicolumn_index(model, column_names, cursor=None):
    """CREATE INDEX db_sample_prod_lab ON db_sample (status_code, production)"""
    cursor = cursor or con.cursor()
    # Get table name and column name as stored in database.
    db_table = model._meta.db_table
    allowed_names = [field.name for field in model._meta.fields]
    for column_name in column_names:
        assert column_name in allowed_names, "Column Name needs to be in model"
    db_column_names = [model._meta.get_field(column_name).column for column_name in column_names]
    db_index = "%s-%s" % (db_table, '_'.join(db_column_names))
    # Create the index.
    cursor.execute(
        "CREATE INDEX \"" + db_index + "\"" +
        " ON \"" + db_table + "\" (%s);" % (','.join(db_column_names)))
    cursor.execute("COMMIT;")


def pg_bulk_update(model, filter_name, update_name,
                   filter_column_data, update_column_data, cursor=None):
    """
    Postgres database utility to quickly update an entire column in a table
    with the values provided in update_column_data matched against
    filter_column_data.

    Model is the Django model to be updated, filter_name is the name of the
    field to match rows to be updated, update_name is the field to be updated
    with data, filter_column_data is the data to test for match with row in
    table (typically primary keys of model) and update_column_data is the
    matching list of values with which to update the table (primary key ids
    if the field is a ForeignKey).
    """
    cursor = cursor or con.cursor()
    # Get table name and column name for filter and update attributes as
    # stored in database.
    db_table = model._meta.db_table
    model_filter = model._meta.get_field(filter_name).column
    model_update = model._meta.get_field(update_name).column
    # Auto-convert tuples to lists.
    if type(filter_column_data) is tuple:
        filter_column_data = list(filter_column_data)
    if type(update_column_data) is tuple:
        update_column_data = list(update_column_data)
    # Input data as Django sanitized parameters,
    cursor.execute(
        "UPDATE " + db_table +
        " SET " + model_update + " = input.update" +
        " FROM (SELECT unnest(%s), unnest(%s)) AS input (filter, update)"
        " WHERE " + model_filter + " = input.filter;", [filter_column_data,
                                                        update_column_data])
    cursor.execute("COMMIT;")
