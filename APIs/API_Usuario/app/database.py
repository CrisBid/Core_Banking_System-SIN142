import os
from cassandra.cluster import Cluster
from cassandra.policies import DCAwareRoundRobinPolicy

CASSANDRA_HOST = os.getenv('CASSANDRA_HOST', 'cassandra')
KEYSPACE = 'core_bank_database'

def get_cassandra_session():
    cluster = Cluster(
        [CASSANDRA_HOST], 
        load_balancing_policy=DCAwareRoundRobinPolicy(local_dc='datacenter1'),
        protocol_version=5
    )  # Altere para o host Cassandra apropriado
    session = cluster.connect(KEYSPACE)  # Altere para o keyspace apropriado
    return session
