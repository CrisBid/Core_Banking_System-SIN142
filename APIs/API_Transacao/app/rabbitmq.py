import pika
import os
import logging

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'user')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'password')

logging.basicConfig(level=logging.INFO)

def get_rabbitmq_connection():
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        logging.info(f"Conexão com RabbitMQ estabelecida com sucesso no host {RABBITMQ_HOST} e porta {RABBITMQ_PORT}.")
        return connection, channel
    except Exception as e:
        logging.error(f"Erro ao conectar com RabbitMQ no host {RABBITMQ_HOST} e porta {RABBITMQ_PORT}: {e}")
        raise e


def get_rabbitmq_external_connection():
    try:
        credentials = pika.PlainCredentials('9d67c2ce-c0e4-4656-bbb8-dd8ff5cc94fd', 'Vini@Calvo2024')
        parameters = pika.ConnectionParameters(host='179.189.94.124', port=9080, credentials=credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        logging.info(f"Conexão com RabbitMQ estabelecida com sucesso no host {'179.189.94.124'} e porta {9080}.")
        return connection, channel
    except Exception as e:
        logging.error(f"Erro ao conectar com RabbitMQ no host {'179.189.94.124'} e porta {9080}: {e}")
        raise e


