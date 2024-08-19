from app.models import ChavePixRequest
from app.rabbitmq import get_rabbitmq_connection
from uuid import UUID, uuid4
import pika
import json

CHAVEPIX_QUEUE = 'chavepix_queue'
CHAVEPIX_RESPONSE_QUEUE = 'chavepix_response_queue'


def enviar_mensagem_para_fila_e_aguardar_resposta(action: str, data: dict):
    try:
        connection, channel = get_rabbitmq_connection()
        channel.queue_declare(queue=CHAVEPIX_QUEUE, durable=True)
        channel.queue_declare(queue=CHAVEPIX_RESPONSE_QUEUE, durable=True)

        correlation_id = str(uuid4())

        message = {
            "action": action,
            **data
        }

        channel.basic_publish(
            exchange='',
            routing_key=CHAVEPIX_QUEUE,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                reply_to=CHAVEPIX_RESPONSE_QUEUE,
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

        channel.basic_consume(queue=CHAVEPIX_RESPONSE_QUEUE, on_message_callback=on_response)

        while response is None:
            connection.process_data_events()

        connection.close()
        return response

    except Exception as e:
        raise Exception(f"Erro ao enviar mensagem para o RabbitMQ: {e}")
    

def criar_chave_pix_service(chave_pix: ChavePixRequest):
    data = {
        "data": chave_pix.dict()
    }
    return enviar_mensagem_para_fila_e_aguardar_resposta("create", data)

def apagar_chave_pix_service(chave_id: UUID):
    data = {
        "chave_id": str(chave_id)
    }
    return enviar_mensagem_para_fila_e_aguardar_resposta("delete", data)

def retornar_chave_pix_service(chave_id: UUID):
    data = {
        "chave_id": str(chave_id)
    }
    return enviar_mensagem_para_fila_e_aguardar_resposta("get", data)

def listar_chaves_pix_service(usuario_id: UUID = None, instituicao_id: UUID = None):
    data = {
        "usuario_id": str(usuario_id) if usuario_id else None,
        "instituicao_id": str(instituicao_id) if instituicao_id else None
    }
    return enviar_mensagem_para_fila_e_aguardar_resposta("list", data)

def buscar_dados_por_chave_service(chave: str):
    data = {
        "chave": chave
    }
    return enviar_mensagem_para_fila_e_aguardar_resposta("find_by_key", data)
