import pika
import json
from uuid import UUID, uuid4
from app.rabbitmq import get_rabbitmq_connection
from app.models import Usuario, UsuarioCreate

USUARIO_QUEUE = 'usuario_queue'
USUARIO_RESPONSE_QUEUE = 'usuario_response_queue'

def enviar_mensagem_para_fila_e_aguardar_resposta(action: str, data: dict):
    try:
        connection, channel = get_rabbitmq_connection()
        channel.queue_declare(queue=USUARIO_QUEUE, durable=True)
        channel.queue_declare(queue=USUARIO_RESPONSE_QUEUE, durable=True)

        correlation_id = str(uuid4())

        message = {
            "action": action,
            **data
        }

        channel.basic_publish(
            exchange='',
            routing_key=USUARIO_QUEUE,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                reply_to=USUARIO_RESPONSE_QUEUE,
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

        channel.basic_consume(queue=USUARIO_RESPONSE_QUEUE, on_message_callback=on_response)

        while response is None:
            connection.process_data_events()

        connection.close()
        return response

    except Exception as e:
        raise Exception(f"Erro ao enviar mensagem para o RabbitMQ: {e}")

def criar_usuario_service(usuario: UsuarioCreate):
    # Verifica se já existe um usuário com o mesmo CPF
    resposta = buscar_usuario_por_cpf_service(usuario.cpf)
    
    print("Resposta da busca", resposta)

    if resposta.get("success") == True:
        # Acesse a chave correta "usuario:"
        usuario_existente = resposta.get("usuario:")  # Corrigido aqui
        if usuario_existente:
            print(f"Usuário com este CPF já está cadastrado: {usuario_existente}")
            return {"success": False, "error": "Usuário com este CPF já está cadastrado", "usuario": usuario_existente}
        else:
            print("Erro: O objeto usuario_existente é None.")
            return {"success": False, "error": "Erro ao recuperar os dados do usuário"}
    else:
        # Se o CPF não estiver em uso, crie o novo usuário
        if resposta.get("error") == "Usuário não encontrado":
            data = {
                "data": usuario.dict()
            }
            print(f"Enviando mensagem para criar usuário: {data}")
            return enviar_mensagem_para_fila_e_aguardar_resposta("create", data)
        else:
            # Se houve um erro inesperado ao buscar o CPF, retorne-o
            print(f"Erro ao verificar CPF: {resposta.get('error')}")
            return {"success": False, "error": resposta.get("error", "Erro ao verificar CPF")}


def apagar_usuario_service(usuario_id: UUID):
    data = {
        "usuario_id": str(usuario_id)
    }
    return enviar_mensagem_para_fila_e_aguardar_resposta("delete", data)

def retornar_usuario_service(usuario_id: UUID):
    data = {
        "usuario_id": str(usuario_id)
    }
    return enviar_mensagem_para_fila_e_aguardar_resposta("get", data)

def listar_usuarios_service(instituicao_id: UUID = None):
    data = {
        "instituicao_id": str(instituicao_id) if instituicao_id else None
    }
    return enviar_mensagem_para_fila_e_aguardar_resposta("list", data)

def buscar_usuario_por_cpf_service(cpf: str):
    data = {
        "cpf": cpf
    }
    resposta = enviar_mensagem_para_fila_e_aguardar_resposta("find_by_cpf", data)
    
    # Certifique-se de que a resposta tenha o campo success
    if resposta.get("success"):
        return resposta
    else:
        return {"success": False, "error": resposta.get("error", "Erro ao buscar usuário")}

