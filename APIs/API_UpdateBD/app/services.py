import pika
import os
import json
import logging
import asyncio
from cassandra.cluster import Cluster
from app.models import TransacaoRequest

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'user')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'password')
SECRET_KEY = os.getenv('SECRET_KEY', 'secret')
RETRY_INTERVAL = 5  # Intervalo de retry em segundos
RABBITMQ_QUEUE = 'transacoes'

CASSANDRA_HOST = os.getenv('CASSANDRA_HOST', 'localhost')
KEYSPACE = 'pix_system'

logging.basicConfig(level=logging.INFO)

class CassandraClient:
    def __init__(self):
        self.cluster = Cluster([CASSANDRA_HOST])
        self.session = self.cluster.connect(KEYSPACE)

async def get_rabbitmq_connection():
    while True:
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
            parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.queue_declare(queue=RABBITMQ_QUEUE)
            return connection, channel
        except pika.exceptions.AMQPConnectionError as e:
            logging.error(f"Erro ao conectar ao RabbitMQ: {e}")
            logging.info(f"Tentando novamente em {RETRY_INTERVAL} segundos...")
            await asyncio.sleep(RETRY_INTERVAL)

def callback(ch, method, properties, body):
    transacao_data = TransacaoRequest.parse_raw(body)
    chave_pix = transacao_data.chave_pix
    valor = transacao_data.valor
    # Verifica chave Pix no Cassandra e realiza a transação entre bancos
    # ...
    ch.basic_ack(delivery_tag=method.delivery_tag)

async def process_transacao():
    connection, channel = await get_rabbitmq_connection()
    channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback)
    logging.info(" [*] Aguardando mensagens na fila. Para sair, pressione CTRL+C")
    channel.start_consuming()

