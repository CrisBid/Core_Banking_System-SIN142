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

def consume_response_from_queue(corr_id):
    connection, channel = get_rabbitmq_connection()
    channel.queue_declare(queue=AUTH_RESPONSE_QUEUE)
    method_frame, header_frame, body = channel.basic_get(AUTH_RESPONSE_QUEUE)
    while not method_frame:
        time.sleep(1)
        method_frame, header_frame, body = channel.basic_get(AUTH_RESPONSE_QUEUE)
    if header_frame.correlation_id == corr_id:
        response = json.loads(body)
        channel.basic_ack(method_frame.delivery_tag)
        connection.close()
        return response
    else:
        channel.basic_nack(method_frame.delivery_tag)
    connection.close()

async def validate_with_auth_service(auth_request: AuthRequest):
    #corr_id = str(uuid.uuid4())
    #request_data = {
    #    "client_id": auth_request.client_id,
    #    "client_secret": auth_request.client_secret,
    #    "corr_id": corr_id
    #}
    #publish_to_queue(request_data, AUTH_QUEUE)
    #response = consume_response_from_queue(corr_id)
    #return {"status": "Autenticação bem-sucedida", "token": corr_id}

    #if "token" in response:
    #    return {"status": "Autenticação bem-sucedida", "token": response["token"]}
    #else:
    #    raise HTTPException(status_code=401, detail="Autenticação falhou")
    try:
        token_response = send_message_to_rabbitmq({"client_id": auth_request.client_id, "client_secret": auth_request.client_secret})
        token_data = json.loads(token_response)
        
        if "error" in token_data:
            raise HTTPException(status_code=401, detail=token_data["error"])

        return {"message": "Autenticação bem-sucedida", **token_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def update_db_service(atualiza_chave_pix: AtualizaChavePix):
    await publish_to_queue(atualiza_chave_pix, ATUALIZACAO_DB_QUEUE)
    return {"status": "Atualização de chave solicitada"}

async def authenticate_request(token: str):
    auth_response = requests.post(AUTH_API_URL, headers={"Authorization": token})
    if auth_response.status_code != 200:
        raise HTTPException(status_code=401, detail="Não autorizado")
    

def send_message_to_rabbitmq(message: dict) -> str:
    connection, channel = get_rabbitmq_connection()
    channel.queue_declare(queue=AUTH_QUEUE, durable=True)
    channel.queue_declare(queue=AUTH_RESPONSE_QUEUE, durable=True)
    
    correlation_id = str(uuid.uuid4())
    
    def on_response(ch, method, properties, body):
        if correlation_id == properties.correlation_id:
            response[0] = body.decode()

    response = [None]
    channel.basic_publish(
        exchange='',
        routing_key=AUTH_QUEUE,
        properties=pika.BasicProperties(
            reply_to=AUTH_RESPONSE_QUEUE,
            correlation_id=correlation_id
        ),
        body=json.dumps(message)
    )

    channel.basic_consume(
        queue=AUTH_RESPONSE_QUEUE,
        on_message_callback=on_response,
        auto_ack=True
    )

    while response[0] is None:
        connection.process_data_events()
    
    connection.close()
    return response[0]

