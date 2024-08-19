from cassandra.cluster import Cluster
import os

CASSANDRA_HOST = os.getenv('CASSANDRA_HOST', 'cassandra')
KEYSPACE = 'core_bank_database'

# Conexão com o Cassandra
cluster = Cluster([CASSANDRA_HOST])  # Altere para o host Cassandra apropriado
session = cluster.connect()

# Criação do keyspace e da tabela, se não existirem
def create_keyspace_and_table():
    # Criação do keyspace
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS core_bank_database 
        WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 1};
    """)
    
    # Seleciona o keyspace
    session.set_keyspace('core_bank_database')
    
    # Criação da tabela institutions
    session.execute("""
        CREATE TABLE IF NOT EXISTS institutions (
            institution_id UUID PRIMARY KEY,
            institution_secret TEXT,
            institution_name TEXT,
            institution_email TEXT,
            created_at TIMESTAMP
        );
    """)
    
    # Criação da tabela usuarios
    session.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            usuario_id UUID PRIMARY KEY,
            nome TEXT,
            email TEXT,
            cpf TEXT,
            telefone TEXT,
            created_at TIMESTAMP
        );
    """)

     # Criação da tabela usuarios_pix
    session.execute("""
        CREATE TABLE IF NOT EXISTS usuarios_pix (
            id UUID PRIMARY KEY,
            usuario_id UUID,
            instituicao_id UUID,
            chave_pix TEXT,
            tipo_chave TEXT,
            created_at TIMESTAMP
        );
    """)

    # Criação da tabela usuarios_pix
    session.execute("""
        CREATE TABLE IF NOT EXISTS transfers (
            id UUID PRIMARY KEY,
            origem_usuario_id UUID,
            origem_instituicao_id UUID,
            destino_usuario_id UUID,
            destino_instituicao_id UUID,
            chave_pix TEXT,
            tipo_chave TEXT,
            valor FLOAT,
            created_at TIMESTAMP
        );
    """)