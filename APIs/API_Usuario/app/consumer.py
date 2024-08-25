import pika
import json
from app.services import (
    criar_usuario,
    apagar_usuario,
    retornar_usuario,
    listar_usuarios,
    retornar_usuario_por_cpf
)
from app.models import Usuario, UsuarioCreate
from app.rabbitmq import get_rabbitmq_connection
from datetime import datetime, timezone
from uuid import UUID
import uuid

USUARIO_QUEUE = 'usuario_queue'
USUARIO_RESPONSE_QUEUE = 'usuario_response_queue'

def process_usuario(ch, method, properties, body):
    message = json.loads(body)

    action = message.get("action")
    resposta = {}

    try:
        if action == "create":
            usuario_data = message.get("data")
            usuario_create = UsuarioCreate(**usuario_data)
            usuario = Usuario(
                usuario_id=uuid.uuid4(),  # Gera o UUID para o novo usuário
                nome=usuario_create.nome,
                email=usuario_create.email,
                cpf=usuario_create.cpf,
                telefone=usuario_create.telefone,
                created_at=str(datetime.now(timezone.utc))
            )
            usuario_criado = criar_usuario(usuario)
    
            # Converte o objeto usuario_criado para dicionário
            usuario_dict = usuario_criado.dict()
            
            # Converte o campo usuario_id para string
            usuario_dict['usuario_id'] = str(usuario_dict['usuario_id'])
            
            resposta = {"status": "Usuário criado com sucesso", "usuario": usuario_dict}

        elif action == "delete":
            usuario_id = UUID(message.get("usuario_id"))
            usuario = apagar_usuario(usuario_id)
            resposta = {"status": "Usuário excluído com sucesso", "usuario:" : usuario.dict()}

        elif action == "get":
            usuario_id = UUID(message.get("usuario_id"))
            usuario = retornar_usuario(usuario_id)
            resposta = usuario.dict() if usuario else {"error": "Usuário não encontrado"}

        elif action == "list":
            usuarios = listar_usuarios()
            resposta = [usuario.dict() for usuario in usuarios]
            for user in resposta:
                user['usuario_id'] = str(user['usuario_id'])

        elif action == "find_by_cpf":
            cpf = message.get("cpf")
            usuario = retornar_usuario_por_cpf(cpf)
            if usuario:
                resposta = usuario.dict()
                resposta['usuario_id'] = str(usuario.usuario_id)
                resposta = {"success" : True, "usuario:": resposta}
            else:
                resposta = {"success" : False, "error": "Usuário não encontrado"}

    except Exception as e:
        resposta = {"error": str(e)}

    # Publicando a resposta na fila de respostas
    ch.basic_publish(
        exchange='',
        routing_key=USUARIO_RESPONSE_QUEUE,
        body=json.dumps(resposta),
        properties=pika.BasicProperties(
            correlation_id=properties.correlation_id
        )
    )
    ch.basic_ack(delivery_tag=method.delivery_tag)

def start_consumer():
    connection, channel = get_rabbitmq_connection()

    channel.queue_declare(queue=USUARIO_QUEUE, durable=True)
    channel.basic_consume(queue=USUARIO_QUEUE, on_message_callback=process_usuario)

    print('Aguardando mensagens...')
    channel.start_consuming()
