from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
import pika
import uuid
import json

app = FastAPI()

SECRET_KEY = "secretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Funções de autenticação
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Configuração do RabbitMQ
RABBITMQ_HOST = 'localhost'
REQUEST_QUEUE = 'token_request_queue'
RESPONSE_QUEUE = 'token_response_queue'

connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
channel = connection.channel()
channel.queue_declare(queue=REQUEST_QUEUE, durable=True)
channel.queue_declare(queue=RESPONSE_QUEUE, durable=True)

def on_request(ch, method, properties, body):
    request = json.loads(body)
    username = request.get("username")
    password = request.get("password")
    
    # Simulação de validação de usuário
    if username != "user" or password != "password":
        ch.basic_publish(
            exchange='',
            routing_key=properties.reply_to,
            properties=pika.BasicProperties(
                correlation_id=properties.correlation_id
            ),
            body=json.dumps({"error": "Invalid username or password"})
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": username}, expires_delta=access_token_expires)
    response = {"access_token": access_token, "token_type": "bearer"}
    
    ch.basic_publish(
        exchange='',
        routing_key=properties.reply_to,
        properties=pika.BasicProperties(
            correlation_id=properties.correlation_id
        ),
        body=json.dumps(response)
    )
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue=REQUEST_QUEUE, on_message_callback=on_request)

@app.on_event("startup")
async def startup_event():
    print("API de autenticação iniciada e ouvindo requisições no RabbitMQ")
    channel.start_consuming()

@app.on_event("shutdown")
async def shutdown_event():
    channel.stop_consuming()
    connection.close()
