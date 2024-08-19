from fastapi import HTTPException
from app.models import AuthRequest
from app.rabbitmq import get_rabbitmq_connection
import pika
import json
import uuid
import time

AUTH_QUEUE = 'auth_queue'
AUTH_RESPONSE_QUEUE = 'auth_response_queue'

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
        token_response = send_message_to_rabbitmq({"institution_id": auth_request.instituicao_id, "institution_secret": auth_request.instituicao_secret})
        token_data = json.loads(token_response)
        
        if "error" in token_data:
            raise HTTPException(status_code=401, detail=token_data["error"])

        return {"message": "Autenticação bem-sucedida", **token_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))