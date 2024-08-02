import pika
import os
import json
import uuid
import jwt
import time
import logging
import asyncio
from fastapi import HTTPException
from app.models import AuthRequest
from app.database import get_cassandra_session

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'user')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'password')
RABBITMQ_QUEUE = 'auth_queue'
AUTH_RESPONSE_QUEUE = 'auth_response_queue'
SECRET_KEY = os.getenv('SECRET_KEY', 'secret')
RETRY_INTERVAL = 5  # Intervalo de retry em segundos

logging.basicConfig(level=logging.INFO)

async def get_rabbitmq_connection():
    while True:
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
            parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials)
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            return connection, channel
        except pika.exceptions.AMQPConnectionError as e:
            logging.error(f"Erro ao conectar ao RabbitMQ: {e}")
            logging.info(f"Tentando novamente em {RETRY_INTERVAL} segundos...")
            await asyncio.sleep(RETRY_INTERVAL)

def validate_auth_request(auth_request: AuthRequest):
    session = get_cassandra_session()
    query = "SELECT * FROM intitucoes WHERE client_id=%s AND client_secret=%s"
    rows = session.execute(query, (auth_request.client_id, auth_request.client_secret))
    if not rows:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    new_token = str(uuid.uuid4())
    return new_token

def publish_response_to_queue(response_data):
    connection, channel = get_rabbitmq_connection()
    channel.queue_declare(queue=AUTH_RESPONSE_QUEUE)
    channel.basic_publish(exchange='', routing_key=AUTH_RESPONSE_QUEUE, body=json.dumps(response_data))
    connection.close()