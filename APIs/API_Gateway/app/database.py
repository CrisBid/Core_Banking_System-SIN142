from cassandra.cluster import Cluster
import os

CASSANDRA_HOST = os.getenv('CASSANDRA_HOST', 'cassandra')
KEYSPACE = 'core_bank_database'

# Conexão com o Cassandra
cluster = Cluster([CASSANDRA_HOST])  # Altere para o host Cassandra apropriado
session = cluster.connect()

# Criação do keyspace e da tabela, se não existirem
def create_keyspace_and_table():
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS core_bank_database 
        WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 1};
    """)
    session.set_keyspace('core_bank_database')
    session.execute("""
        CREATE TABLE IF NOT EXISTS institutions (
            id UUID PRIMARY KEY,
            name TEXT,
            api_key TEXT,
            created_at TIMESTAMP
        );
    """)