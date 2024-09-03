from fastapi import FastAPI, HTTPException
from app.database import get_cassandra_session
from app.rabbitmq import get_rabbitmq_connection, get_rabbitmq_external_connection
from datetime import datetime, timedelta, timezone
from cassandra.cluster import Session
from uuid import UUID
import pika
import json
import logging
import time

TRANSACTION_QUEUE = 'transaction_queue'
TRANSACTION_RESPONSE_QUEUE = 'transaction_response_queue'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Estabelecendo conexão com RabbitMQ...")
connection, channel = get_rabbitmq_connection()
channel.queue_declare(queue=TRANSACTION_QUEUE, durable=True)
channel.queue_declare(queue=TRANSACTION_RESPONSE_QUEUE, durable=True)
logger.info("Conexão com RabbitMQ estabelecida e filas declaradas.")

def process_transacao(ch, method, properties, body):
    logger.info(f"Recebida nova transação: {body}")
    session: Session = get_cassandra_session()
    transacao = json.loads(body)

    try:
        usuario_origem = transacao["data"]["usuario_id"]
        instituicao_origem = transacao["data"]["instituicao_id"]
        chave_pix = transacao["data"]["chave_pix"]
        valor = transacao["data"]["valor"]
        
        logger.info("Buscando dados do destinatário na tabela usuarios_pix...")
        query = """
            SELECT usuario_id, instituicao_id, tipo_chave 
            FROM usuarios_pix 
            WHERE chave_pix = %s ALLOW FILTERING
        """
        result = session.execute(query, (chave_pix,)).one()
        
        if result:
            usuario_destino = result.usuario_id
            instituicao_destino = result.instituicao_id
            tipo_chave = result.tipo_chave
            logger.info(f"Dados do destinatário encontrados: {result}")
        else:
            logger.error("Chave PIX não encontrada.")
            raise ValueError("Chave PIX não encontrada")

        if instituicao_origem == instituicao_destino:
            logger.info("Processando transação interna...")
            try:
                # Lógica de processamento da transação interna
                logger.info(f"Processando transação interna de {instituicao_origem} para {instituicao_destino}: {transacao}")
                
                # Simulação de sucesso
                sucesso = True  
                
                if sucesso:
                    logger.info(f"Transação interna processada com sucesso entre {instituicao_origem} e {instituicao_destino}")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    logger.error(f"Falha ao processar transação interna entre {instituicao_origem} e {instituicao_destino}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            
            except Exception as e:
                logger.error(f"Erro ao processar transação interna: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        else:
            logger.info("Processando transação externa...")
            try:
                external_connection, external_channel = get_rabbitmq_external_connection()

                logger.info(f"Declarando fila transacao_{instituicao_origem}_queue no RabbitMQ externo...")
                external_channel.queue_declare(queue=f"transacao_{instituicao_origem}_queue", durable=True)

                logger.info(f"Enviando transação para o banco de origem {instituicao_origem}...")
                external_channel.basic_publish(
                    exchange='',
                    routing_key=f"transacao_{instituicao_origem}_queue",
                    body=json.dumps({
                        "action": "transfer_outbound",
                        "usuario_origem": str(usuario_origem),
                        "usuario_destino": str(usuario_destino),
                        "instituicao_origem": str(instituicao_origem),
                        "instituicao_destino": str(instituicao_destino),
                        "chave_pix": chave_pix,
                        "tipo_chave": tipo_chave,
                        "valor": valor
                    }),
                    properties=pika.BasicProperties(
                        reply_to=f"transacao_{instituicao_origem}_response_queue",
                        correlation_id=properties.correlation_id,
                        delivery_mode=2,
                    )
                )
                
                logger.info("Aguardando resposta do banco de origem...")
                response = None
                timeout = 30
                start_time = time.time()

                def on_response(ch, method, properties, body):
                    nonlocal response
                    if properties.correlation_id == properties.correlation_id:
                        response = json.loads(body)
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        logger.info(f"Resposta do banco de origem recebida: {response}")

                external_channel.basic_consume(
                    queue=f"transacao_{instituicao_origem}_response_queue",
                    on_message_callback=on_response,
                    auto_ack=False
                )

                while response is None and (time.time() - start_time) < timeout:
                    external_connection.process_data_events(time_limit=1)

                if response is None:
                    logger.error(f"Timeout ao aguardar a resposta do banco de origem {instituicao_origem}")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return

                if response.get("sucesso"):
                    logger.info(f"Transação externa processada com sucesso pelo banco de origem {instituicao_origem}")
                    
                    logger.info(f"Enviando transação para o banco de destino {instituicao_destino}...")
                    external_channel.basic_publish(
                        exchange='',
                        routing_key=f"transacao_{instituicao_destino}_queue",
                        body=json.dumps({
                            "action": "transfer_inbound",
                            "usuario_origem": str(usuario_origem),
                            "usuario_destino": str(usuario_destino),
                            "instituicao_origem": str(instituicao_origem),
                            "instituicao_destino": str(instituicao_destino),
                            "chave_pix": chave_pix,
                            "tipo_chave": tipo_chave,
                            "valor": valor
                        }),
                        properties=pika.BasicProperties(
                            reply_to=f"transacao_{instituicao_destino}_response_queue",
                            correlation_id=properties.correlation_id,
                            delivery_mode=2,
                        )
                    )

                    logger.info("Aguardando resposta do banco de destino...")
                    response_destino = None
                    timeout = 30
                    start_time = time.time()

                    def on_response_destino(ch, method, properties, body):
                        nonlocal response_destino
                        if properties.correlation_id == properties.correlation_id:
                            response_destino = json.loads(body)
                            ch.basic_ack(delivery_tag=method.delivery_tag)
                            logger.info(f"Resposta do banco de destino recebida: {response_destino}")

                    external_channel.basic_consume(
                        queue=f"transacao_{instituicao_destino}_response_queue",
                        on_message_callback=on_response_destino,
                        auto_ack=False
                    )

                    while response_destino is None and (time.time() - start_time) < timeout:
                        external_connection.process_data_events(time_limit=1)

                    if response_destino is None:
                        logger.error(f"Timeout ao aguardar a resposta do banco de destino {instituicao_destino}")
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        return

                    if response_destino.get("sucesso"):
                        logger.info(f"Transação externa processada com sucesso pelo banco de destino {instituicao_destino}")
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    else:
                        logger.error(f"Falha ao processar transação externa pelo banco de destino {instituicao_destino}")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                
                else:
                    logger.error(f"Falha ao processar transação externa pelo banco de origem {instituicao_origem}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

                external_connection.close()

            except Exception as e:
                logger.error(f"Erro ao processar transação externa: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    except Exception as e:
        logger.error(f"Erro ao processar transação: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

channel.basic_consume(queue=TRANSACTION_QUEUE, on_message_callback=process_transacao)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    logger.info("API de autenticação iniciada e ouvindo requisições no RabbitMQ")
    channel.start_consuming()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Encerrando consumo de mensagens e fechando conexão com RabbitMQ")
    channel.stop_consuming()
    connection.close()
