from fastapi import FastAPI, HTTPException
from app.database import get_cassandra_session
from app.rabbitmq import get_rabbitmq_connection , get_rabbitmq_external_connection
from datetime import datetime, timedelta, timezone
from cassandra.cluster import Session
from uuid import UUID
import pika
import json
import logging

TRANSACTION_QUEUE = 'transaction_queue'
TRANSACTION_RESPONSE_QUEUE = 'transaction_response_queue'

TRANSACTION_EXTERNAL_ORIGIN_QUEUE = 'transaction_external_origin_queue'
TRANSACTION_EXTERNAL_RESPONSE_ORIGIN_QUEUE = 'transaction_external_response_origin_queue'

TRANSACTION_EXTERNAL_DESTINATION_QUEUE = 'transaction_external_destination_queue'
TRANSACTION_EXTERNAL_RESPONSE_DESTINATION_QUEUE = 'transaction_external_response_destination_queue'

logging.basicConfig(level=logging.INFO)

connection, channel = get_rabbitmq_connection()
channel.queue_declare(queue=TRANSACTION_QUEUE, durable=True)
channel.queue_declare(queue=TRANSACTION_RESPONSE_QUEUE, durable=True)

connection, channel_external = get_rabbitmq_external_connection()
channel_external.queue_declare(queue=TRANSACTION_EXTERNAL_ORIGIN_QUEUE, durable=True)
channel_external.queue_declare(queue=TRANSACTION_EXTERNAL_RESPONSE_ORIGIN_QUEUE, durable=True)

channel_external.queue_declare(queue=TRANSACTION_EXTERNAL_DESTINATION_QUEUE, durable=True)
channel_external.queue_declare(queue=TRANSACTION_EXTERNAL_RESPONSE_DESTINATION_QUEUE, durable=True)

def process_transacao(ch, method, properties, body):
    session: Session = get_cassandra_session()
    transacao = json.loads(body)
    
    usuario_origem = transacao["usuario_origem"]
    usuario_destino = transacao["usuario_destino"]
    instituicao_origem = transacao["instituicao_origem"]
    instituicao_destino = transacao["instituicao_destino"]
    chave_pix = transacao["chave_pix"]
    tipo_chave = transacao["tipo_chave"]
    valor = transacao["valor"]
    
    if instituicao_origem == instituicao_destino:
        # Transação interna
        try:
            # Processa a transação internamente
            print(f"Processando transação interna de {instituicao_origem} para {instituicao_destino}: {transacao}")
            # Aqui você faria a lógica de processamento da transação interna no banco de dados Cassandra
            
            # Simulação de sucesso
            sucesso = True  
            
            if sucesso:
                print(f"Transação interna processada com sucesso entre {instituicao_origem} e {instituicao_destino}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                print(f"Falha ao processar transação interna entre {instituicao_origem} e {instituicao_destino}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        except Exception as e:
            logging.error(f"Erro ao processar transação interna: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    else:
        # Transação externa
        try:
            # Conecta ao RabbitMQ externo
            external_connection, external_channel = get_rabbitmq_external_connection()

            # Envia a transação para o banco de origem
            external_channel.basic_publish(
                exchange='',
                routing_key=f"{instituicao_origem}_to_{instituicao_destino}_queue",  # Nome dinâmico da fila
                body=json.dumps({
                    "action": "transfer_outbound",
                    "usuario_origem": usuario_origem,
                    "usuario_destino": usuario_destino,
                    "instituicao_origem": instituicao_origem,
                    "instituicao_destino": instituicao_destino,
                    "chave_pix": chave_pix,
                    "tipo_chave": tipo_chave,
                    "valor": valor
                }),
                properties=pika.BasicProperties(
                    reply_to=TRANSACTION_EXTERNAL_RESPONSE_ORIGIN_QUEUE,
                    correlation_id=properties.correlation_id,
                    delivery_mode=2,
                )
            )

            # Aguarda a resposta do banco de origem
            response = None

            def on_response(ch, method, properties, body):
                nonlocal response
                if properties.correlation_id == properties.correlation_id:
                    response = json.loads(body)
                    ch.basic_ack(delivery_tag=method.delivery_tag)

            external_channel.basic_consume(queue=TRANSACTION_EXTERNAL_RESPONSE_ORIGIN_QUEUE, on_message_callback=on_response)

            while response is None:
                external_connection.process_data_events()

            # Verifica a resposta do banco de origem
            if response.get("sucesso"):
                print(f"Transação externa processada com sucesso pelo banco de origem {instituicao_origem}")
                
                # Envia a transação para o banco de destino
                external_channel.basic_publish(
                    exchange='',
                    routing_key=f"{instituicao_destino}_from_{instituicao_origem}_queue",  # Nome dinâmico da fila
                    body=json.dumps({
                        "action": "transfer_inbound",
                        "usuario_origem": usuario_origem,
                        "usuario_destino": usuario_destino,
                        "instituicao_origem": instituicao_origem,
                        "instituicao_destino": instituicao_destino,
                        "chave_pix": chave_pix,
                        "tipo_chave": tipo_chave,
                        "valor": valor
                    }),
                    properties=pika.BasicProperties(
                        reply_to=TRANSACTION_EXTERNAL_RESPONSE_DESTINATION_QUEUE,
                        correlation_id=properties.correlation_id,
                        delivery_mode=2,
                    )
                )

                # Aguarda a resposta do banco de destino
                response_destino = None

                def on_response_destino(ch, method, properties, body):
                    nonlocal response_destino
                    if properties.correlation_id == properties.correlation_id:
                        response_destino = json.loads(body)
                        ch.basic_ack(delivery_tag=method.delivery_tag)

                external_channel.basic_consume(queue=TRANSACTION_EXTERNAL_RESPONSE_DESTINATION_QUEUE, on_message_callback=on_response_destino)

                while response_destino is None:
                    external_connection.process_data_events()

                if response_destino.get("sucesso"):
                    print(f"Transação externa processada com sucesso pelo banco de destino {instituicao_destino}")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    print(f"Falha ao processar transação externa pelo banco de destino {instituicao_destino}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            else:
                print(f"Falha ao processar transação externa pelo banco de origem {instituicao_origem}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            external_connection.close()

        except Exception as e:
            logging.error(f"Erro ao processar transação externa: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


channel.basic_consume(queue=TRANSACTION_QUEUE, on_message_callback=process_transacao)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    print("API de autenticação iniciada e ouvindo requisições no RabbitMQ")
    channel.start_consuming()

@app.on_event("shutdown")
async def shutdown_event():
    channel.stop_consuming()
    connection.close()

