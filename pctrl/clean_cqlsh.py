import os
import sqlite3
from cassandra.cluster import Cluster
from cassandra.query import dict_factory
from StringIO import StringIO
import globs

cluster = Cluster(
                contact_points=globs.CASSANDRA_HOST
                )
session = cluster.connect(globs.CASSANDRA_SPACE)
session.row_factory = dict_factory

#initialize table name using ip + type(local, input, output)
# Use cassandra session object
query = "drop keyspace demo;"
prep = session.prepare(query)
session.execute(prep)

query = "CREATE KEYSPACE demo WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 };"
prep = session.prepare(query)
session.execute(prep)
