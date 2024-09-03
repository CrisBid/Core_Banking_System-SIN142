from app.models import ChavePixRequest, ChavePix
from app.database import get_cassandra_session
from cassandra.cluster import Session
from uuid import UUID, uuid4
import pika
import os
import json
import logging

logging.basicConfig(level=logging.INFO)

def criar_chave_pix_service(chave_pix: ChavePixRequest) -> ChavePixRequest:
    session: Session = get_cassandra_session()

    query = """
    INSERT INTO usuarios_pix (id, chave_pix, tipo_chave, usuario_id, instituicao_id, created_at)
    VALUES (%s, %s, %s, %s, %s, toTimestamp(now()))
    """
    session.execute(query, (
        chave_pix.id,
        chave_pix.chave_pix,
        chave_pix.tipo_chave,
        chave_pix.usuario_id,
        chave_pix.instituicao_id
    ))

    return chave_pix

def apagar_chave_pix_service(chave_id: UUID) -> None:
    session: Session = get_cassandra_session()

    query = "DELETE FROM usuarios_pix WHERE id = %s"
    session.execute(query, (chave_id,))

def retornar_chave_pix_service(chave_id: UUID) -> ChavePix:
    session: Session = get_cassandra_session()

    query = "SELECT id, chave_pix, tipo_chave, usuario_id, instituicao_id, created_at FROM usuarios_pix WHERE chave_id = %s"
    row = session.execute(query, (chave_id,)).one()

    if row is None:
        return None

    return ChavePix(
        id=str(row.id),
        chave=row.chave,
        tipo_chave=row.tipo_chave,
        usuario_id=row.usuario_id,
        instituicao_id=row.instituicao_id,
        created_at=row.created_at.isoformat() if row.created_at else None
    )

def listar_chaves_pix_service(usuario_id: str = None, instituicao_id: str = None) -> list:
    session: Session = get_cassandra_session()

    if usuario_id:
        usuario_uuid = UUID(usuario_id)
        query = "SELECT id, chave_pix, tipo_chave, usuario_id, instituicao_id, created_at FROM usuarios_pix WHERE usuario_id = %s ALLOW FILTERING"
        rows = session.execute(query, (usuario_uuid,))
    elif instituicao_id:
        instituicao_uuid = UUID(instituicao_id)
        query = "SELECT id, chave_pix, tipo_chave, usuario_id, instituicao_id, created_at FROM usuarios_pix WHERE instituicao_id = %s ALLOW FILTERING"
        rows = session.execute(query, (instituicao_uuid,))
    else:
        query = "SELECT id, chave_pix, tipo_chave, usuario_id, instituicao_id, created_at FROM usuarios_pix"
        rows = session.execute(query)

    chaves = []
    for row in rows:
        chaves.append(ChavePix(
            id=str(row.id),  # Convertendo UUID para string
            chave_pix=row.chave_pix,
            tipo_chave=row.tipo_chave,
            usuario_id=str(row.usuario_id),  # Convertendo UUID para string
            instituicao_id=str(row.instituicao_id),  # Convertendo UUID para string
            created_at=str(row.created_at.isoformat() if row.created_at else None ) # Convertendo datetime para string no formato ISO
        ))

    return chaves

def buscar_chave_pix_service(chave: str) -> dict:
    session: Session = get_cassandra_session()

    # Query para buscar a chave Pix
    query_chave = """
    SELECT id, chave_pix, tipo_chave, usuario_id, instituicao_id, created_at
    FROM usuarios_pix
    WHERE chave_pix = %s ALLOW FILTERING
    """

    result_chave = session.execute(query_chave, (chave,)).one()

    if not result_chave:
        return None
    
    # Query para buscar os detalhes do usuário
    query_usuario = """
    SELECT usuario_id, nome, email, cpf, telefone, created_at
    FROM usuarios
    WHERE usuario_id = %s
    """

    result_usuario = session.execute(query_usuario, (result_chave.usuario_id,)).one()

    if not result_usuario:
        return None

    # Query para buscar os detalhes da instituição
    query_instituicao = """
    SELECT institution_id, institution_name, institution_email, created_at
    FROM institutions
    WHERE institution_id = %s
    """

    result_instituicao = session.execute(query_instituicao, (result_chave.instituicao_id,)).one()

    if not result_instituicao:
        return None

    # Montando o retorno com os dados completos, convertendo UUIDs para string e datetime para ISO format
    return {
        "chave_pix": {
            "id": str(result_chave.id),
            "chave_pix": result_chave.chave_pix,
            "tipo_chave": result_chave.tipo_chave,
            "created_at": result_chave.created_at.isoformat() if result_chave.created_at else None
        },
        "usuario": {
            "usuario_id": str(result_usuario.usuario_id),
            "nome": result_usuario.nome,
            "email": result_usuario.email,
            "cpf": result_usuario.cpf,
            "telefone": result_usuario.telefone,
            "created_at": result_usuario.created_at.isoformat() if result_usuario.created_at else None
        },
        "instituicao": {
            "institution_id": str(result_instituicao.institution_id),
            "nome": result_instituicao.institution_name,
            "email": result_instituicao.institution_email,
            "created_at": result_instituicao.created_at.isoformat() if result_instituicao.created_at else None
        }
    }


