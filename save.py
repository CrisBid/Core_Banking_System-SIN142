import requests
import pika
import os
import json
import uuid
import time
from fastapi import HTTPException
import logging
from app.models import TransacaoRequest, AuthRequest, AtualizaChavePix

# Configurações do RabbitMQ
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'user')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'password')
TRANSACOES_QUEUE = 'transacoes_queue'
AUTH_QUEUE = 'auth_queue'
AUTH_RESPONSE_QUEUE = 'auth_response_queue'
ATUALIZACAO_DB_QUEUE = 'atualizacao_db_queue'
AUTH_API_URL = "http://auth-service/validate"

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
    
# Inicializa a conexão ao iniciar a aplicação
connection, channel = get_rabbitmq_connection()

# Fechar a conexão ao encerrar a aplicação
def close_rabbitmq_connection():
    connection.close()
    logging.info("Conexão com RabbitMQ fechada.")

async def publish_to_queue(data, queue):
    channel.queue_declare(queue=queue)
    channel.basic_publish(exchange='', routing_key=queue, body=json.dumps(data.dict()))

async def update_db_service(atualiza_chave_pix: AtualizaChavePix):
    await publish_to_queue(atualiza_chave_pix, ATUALIZACAO_DB_QUEUE)
    return {"status": "Atualização de chave solicitada"}

async def authenticate_request(token: str):
    auth_response = requests.post(AUTH_API_URL, headers={"Authorization": token})
    if auth_response.status_code != 200:
        raise HTTPException(status_code=401, detail="Não autorizado")
    

