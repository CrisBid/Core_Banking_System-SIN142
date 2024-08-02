import os
from cassandra.cluster import Cluster

CASSANDRA_HOST = os.getenv('CASSANDRA_HOST', 'cassandra')
KEYSPACE = 'core_bank_databse'

def get_cassandra_session():
    cluster = Cluster([CASSANDRA_HOST])  # Altere para o host Cassandra apropriado
    session = cluster.connect(KEYSPACE)  # Altere para o keyspace apropriado
    return session
