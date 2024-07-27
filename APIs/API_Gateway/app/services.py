import requests
import pika
import os
import json
from fastapi import HTTPException
from app.models import TransacaoRequest, AuthRequest, AtualizaChavePix

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'user')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'password')
TRANSACOES_QUEUE = 'transacoes'
AUTH_QUEUE = 'auth_queue'
ATUALIZACAO_DB_QUEUE = 'atualizacao_db_queue'
AUTH_API_URL = "http://auth-service/validate"

def get_rabbitmq_connection():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    return connection, channel

async def authenticate_request(token: str):
    auth_response = requests.post(AUTH_API_URL, headers={"Authorization": token})
    if auth_response.status_code != 200:
        raise HTTPException(status_code=401, detail="Não autorizado")

async def publish_to_queue(data, queue):
    connection, channel = get_rabbitmq_connection()
    channel.queue_declare(queue=queue)
    channel.basic_publish(exchange='', routing_key=queue, body=json.dumps(data.dict()))
    connection.close()

async def validate_with_auth_service(auth_request: AuthRequest):
    #await publish_to_queue(auth_request, AUTH_QUEUE)
    return {"status": "Autenticação solicitada", "token" : "156155615156"}

async def update_db_service(atualiza_chave_pix: AtualizaChavePix):
    await publish_to_queue(atualiza_chave_pix, ATUALIZACAO_DB_QUEUE)
    return {"status": "Atualização de chave solicitada"}

