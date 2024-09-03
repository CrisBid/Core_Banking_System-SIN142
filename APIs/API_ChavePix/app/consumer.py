import pika
import json
from app.services import (
    criar_chave_pix_service,
    apagar_chave_pix_service,
    retornar_chave_pix_service,
    listar_chaves_pix_service,
    buscar_chave_pix_service
)
from app.models import ChavePixRequest
from app.rabbitmq import get_rabbitmq_connection
from uuid import UUID

CHAVEPIX_QUEUE = 'chavepix_queue'
CHAVEPIX_RESPONSE_QUEUE = 'chavepix_response_queue'

def process_chave_pix(ch, method, properties, body):
    message = json.loads(body)

    action = message.get("action")
    resposta = {}

    try:
        if action == "create":
            chave_pix_data = message.get("data")
            chave_pix = ChavePixRequest(**chave_pix_data)
            resposta_request = criar_chave_pix_service(chave_pix)

             # Converte o objeto usuario_criado para dicionário
            pix_dict = resposta_request.dict()
            
            # Converte o campo usuario_id para string
            pix_dict['id'] = str(pix_dict['id'])
            pix_dict['usuario_id'] = str(pix_dict['usuario_id'])
            pix_dict['instituicao_id'] = str(pix_dict['instituicao_id'])

            resposta = {"status": "Chave PIX criada com sucesso", "data":pix_dict}

        elif action == "delete":
            chave_id = UUID(message.get("chave_id"))
            apagar_chave_pix_service(chave_id)
            resposta = {"status": "Chave PIX excluída com sucesso"}

        elif action == "get":
            chave_id = UUID(message.get("chave_id"))
            chave_pix = retornar_chave_pix_service(chave_id)
            resposta = chave_pix.dict() if chave_pix else {"error": "Chave PIX não encontrada"}

        elif action == "list":
            usuario_id = message.get("usuario_id")
            instituicao_id = message.get("instituicao_id")
            chaves_pix = listar_chaves_pix_service(usuario_id, instituicao_id)
            resposta = [chave.dict() for chave in chaves_pix]
            for chave in resposta:
                chave['id'] = str(chave['id'])
                chave['usuario_id'] = str(chave['usuario_id'])
                chave['instituicao_id'] = str(chave['instituicao_id'])

        elif action == "find_by_key":
            chave = message.get("chave")
            # Simulação de uma consulta ao banco de dados para encontrar a chave
            resposta = buscar_chave_pix_service(chave)

    except Exception as e:
        resposta = {"error": str(e)}

    # Publicando a resposta na fila CHAVEPIX_RESPONSE_QUEUE
    ch.basic_publish(
        exchange='',
        routing_key=CHAVEPIX_RESPONSE_QUEUE,
        body=json.dumps(resposta),
        properties=pika.BasicProperties(
            correlation_id=properties.correlation_id
        )
    )
    ch.basic_ack(delivery_tag=method.delivery_tag)

def start_consumer():
    connection, channel = get_rabbitmq_connection()

    channel.queue_declare(queue=CHAVEPIX_QUEUE, durable=True)
    channel.basic_consume(queue=CHAVEPIX_QUEUE, on_message_callback=process_chave_pix)

    print('Aguardando mensagens...')
    channel.start_consuming()
