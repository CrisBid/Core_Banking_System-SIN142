from fastapi import HTTPException
import pika
import json
from app.models import AuthRequest
from app.services import validate_auth_request, publish_response_to_queue, get_rabbitmq_connection

AUTH_QUEUE = 'auth_queue'
AUTH_RESPONSE_QUEUE = 'auth_response_queue'

def consume_auth_requests():
    connection, channel = get_rabbitmq_connection()

    def callback(ch, method, properties, body):
        auth_request_data = json.loads(body)
        auth_request = AuthRequest(
            client_id=auth_request_data["client_id"],
            client_secret=auth_request_data["client_secret"]
        )
        try:
            new_token = validate_auth_request(auth_request)
            response_data = {"client_id": auth_request.client_id, "token": new_token}
        except HTTPException as e:
            response_data = {"client_id": auth_request.client_id, "error": str(e.detail)}

        #response_properties = pika.BasicProperties(correlation_id=auth_request_data["corr_id"])
        ch.basic_publish(
            exchange='',
            routing_key=AUTH_RESPONSE_QUEUE,
            body=json.dumps(response_data),
           # properties=response_properties
        )

    channel.queue_declare(queue=AUTH_QUEUE)
    channel.basic_consume(queue=AUTH_QUEUE, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()
