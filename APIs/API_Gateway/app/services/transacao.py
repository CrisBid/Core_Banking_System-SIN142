from app.models import TransacaoRequest
from app.rabbitmq import get_rabbitmq_connection
from uuid import UUID, uuid4
import pika
import json

TRANSACTION_QUEUE = 'transaction_queue'
TRANSACTION_RESPONSE_QUEUE = 'transaction_response_queue'


def enviar_mensagem_para_fila_e_aguardar_resposta(action: str, data: dict):
    try:
        connection, channel = get_rabbitmq_connection()
        channel.queue_declare(queue=TRANSACTION_QUEUE, durable=True)
        channel.queue_declare(queue=TRANSACTION_RESPONSE_QUEUE, durable=True)

        correlation_id = str(uuid4())

        message = {
            "action": action,
            **data
        }

        channel.basic_publish(
            exchange='',
            routing_key=TRANSACTION_QUEUE,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                reply_to=TRANSACTION_RESPONSE_QUEUE,
                correlation_id=correlation_id,
                delivery_mode=2,
            )
        )

        response = None

        def on_response(ch, method, properties, body):
            nonlocal response
            if properties.correlation_id == correlation_id:
                response = json.loads(body)
                ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(queue=TRANSACTION_RESPONSE_QUEUE, on_message_callback=on_response)

        while response is None:
            connection.process_data_events()

        connection.close()
        return response

    except Exception as e:
        raise Exception(f"Erro ao enviar mensagem para o RabbitMQ: {e}")
    

def criar_transacao_service(request: TransacaoRequest):
    data = {
        "data": request.dict()
    }
    return enviar_mensagem_para_fila_e_aguardar_resposta("create", data)
