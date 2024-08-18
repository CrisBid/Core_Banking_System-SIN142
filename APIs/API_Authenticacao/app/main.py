from fastapi import FastAPI, HTTPException
import pika
import os
import json
import uuid
import time
import logging
import asyncio
import jwt
from uuid import UUID
from datetime import datetime, timedelta, timezone
from app.models import AuthRequest
from app.database import get_cassandra_session
from cassandra.cluster import Session

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'user')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'password')

AUTH_QUEUE = 'auth_queue'
AUTH_RESPONSE_QUEUE = 'auth_response_queue'

SECRET_KEY = "secretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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
    

# Funções de autenticação
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # Codificação com PyJWT
    return encoded_jwt

connection, channel = get_rabbitmq_connection()
channel.queue_declare(queue=AUTH_QUEUE, durable=True)
channel.queue_declare(queue=AUTH_RESPONSE_QUEUE, durable=True)

def validate_auth_request(ch, method, properties, body):
    request = json.loads(body)
    institution_id = request.get("institution_id")
    institution_secret = request.get("institution_secret")
    
    if not institution_id or not institution_secret:
        ch.basic_publish(
            exchange='',
            routing_key=properties.reply_to,
            properties=pika.BasicProperties(
                correlation_id=properties.correlation_id
            ),
            body=json.dumps({"error": "Missing institution_id or institution_secret"})
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
    
    try:
        # Convertendo institution_id para UUID
        institution_id = UUID(institution_id)

        # Obtém a sessão do Cassandra
        session: Session = get_cassandra_session()
        
        # Consulta no banco de dados para validar o institution_id e institution_secret
        query = "SELECT institution_id, institution_secret FROM institutions WHERE institution_id = %s"
        row = session.execute(query, (institution_id,)).one()
        
        if row is None or row.institution_secret != institution_secret:
            ch.basic_publish(
                exchange='',
                routing_key=properties.reply_to,
                properties=pika.BasicProperties(
                    correlation_id=properties.correlation_id
                ),
                body=json.dumps({"error": "Invalid institution_id or institution_secret"})
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        # Se a validação for bem-sucedida, cria o token JWT
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": str(institution_id)}, expires_delta=access_token_expires)
        
        response = {
            "access_token": access_token,
            "token_type": "bearer",
            "validateTime": int(access_token_expires.total_seconds())
        }
        
        ch.basic_publish(
            exchange='',
            routing_key=properties.reply_to,
            properties=pika.BasicProperties(
                correlation_id=properties.correlation_id
            ),
            body=json.dumps(response)
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    except Exception as e:
        logging.error(f"Erro ao validar a instituição no Cassandra: {e}")
        ch.basic_publish(
            exchange='',
            routing_key=properties.reply_to,
            properties=pika.BasicProperties(
                correlation_id=properties.correlation_id
            ),
            body=json.dumps({"error": "Internal server error"})
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_consume(queue=AUTH_QUEUE, on_message_callback=validate_auth_request)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    print("API de autenticação iniciada e ouvindo requisições no RabbitMQ")
    channel.start_consuming()

@app.on_event("shutdown")
async def shutdown_event():
    channel.stop_consuming()
    connection.close()
