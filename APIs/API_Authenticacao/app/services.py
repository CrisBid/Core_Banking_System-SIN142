import pika
import os
import json
import jwt
import time
import logging
import asyncio
from cassandra.cluster import Cluster
from app.models import AuthRequest

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_QUEUE = 'auth_queue'
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'user')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'password')
SECRET_KEY = os.getenv('SECRET_KEY', 'secret')
RETRY_INTERVAL = 5  # Intervalo de retry em segundos

CASSANDRA_HOST = os.getenv('CASSANDRA_HOST', 'localhost')
KEYSPACE = 'pix_system'

logging.basicConfig(level=logging.INFO)

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
    auth_request = AuthRequest.parse_raw(body)
    token = generate_token(auth_request)
    # Aqui você pode enviar o token de volta ao gateway ou processar conforme necessário
    ch.basic_ack(delivery_tag=method.delivery_tag)

def generate_token(auth_request: AuthRequest):
    if auth_request.client_id == "valid_id" and auth_request.client_secret == "valid_secret":
        token = jwt.encode({"exp": time.time() + 600}, SECRET_KEY, algorithm="HS256")
        return {"token": token}
    else:
        return {"error": "Credenciais inválidas"}

async def process_authentication():
    connection, channel = await get_rabbitmq_connection()
    channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback)
    logging.info(" [*] Aguardando mensagens na fila. Para sair, pressione CTRL+C")
    channel.start_consuming()
