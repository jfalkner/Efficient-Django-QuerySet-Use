from datetime import datetime
from django.db import connection as con
import sqlparse


def start():
    global start_time
    global query_count
    start_time = datetime.now()
    query_count = len(con.queries)

def finish():
    print "Time: %s"%(datetime.now()-start_time)
    print "Queries: %s"%(len(con.queries)-query_count)

    for query in con.queries[query_count:]:
        print sqlparse.format(query['sql'], reindent=True, keyword_case='upper')
