from fastapi import APIRouter, Request, Depends, HTTPException
#from app.services import update_db_service
from app.services.auth import validate_with_auth_service
from app.services.chavepix import (
    criar_chave_pix_service,
    apagar_chave_pix_service,
    retornar_chave_pix_service,
    listar_chaves_pix_service,
    buscar_dados_por_chave_service
)
from app.services.usuario import (
    criar_usuario_service,
    apagar_usuario_service,
    retornar_usuario_service,
    listar_usuarios_service,
    buscar_usuario_por_cpf_service
)
from app.models import TransacaoRequest, AuthRequest, ChavePixRequest, Usuario, UsuarioCreate
from app.auth import verify_token  # Importe a função de verificação de token

from uuid import UUID

router = APIRouter()

@router.post("/auth/")
async def autenticar(auth_request: AuthRequest):
    response = await validate_with_auth_service(auth_request)
    return response

@router.post("/transacao/")
async def criar_transacao(request: Request, transacao_request: TransacaoRequest, institution_id: str = Depends(verify_token)):
    # Validação do token já ocorreu, se chegou aqui, o token é válido
    #await publish_to_queue(transacao_request, 'transacoes')
    return {"status": "Transação encaminhada"}

#@router.post("/chave_pix/")
#async def atualiza_chave(atualiza_chave_pix: AtualizaChavePix, institution_id: str = Depends(verify_token)):
    # Validação do token já ocorreu, se chegou aqui, o token é válido
    #response = await update_db_service(atualiza_chave_pix)
    #return response


@router.post("/chave_pix/")
async def criar_chave_pix(chave_pix: ChavePixRequest, institution_id: str = Depends(verify_token)):
    try:
        resposta = criar_chave_pix_service(chave_pix)
        return resposta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar a chave PIX: {e}")

@router.delete("/chave_pix/{chave_id}")
async def apagar_chave_pix(chave_id: UUID, institution_id: str = Depends(verify_token)):
    try:
        resposta = apagar_chave_pix_service(chave_id)
        return resposta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao apagar a chave PIX: {e}")

@router.get("/chave_pix/{chave_id}")
async def retornar_chave_pix(chave_id: UUID, institution_id: str = Depends(verify_token)):
    try:
        resposta = retornar_chave_pix_service(chave_id)
        return resposta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao retornar a chave PIX: {e}")

@router.get("/chave_pix/")
async def listar_chaves_pix(usuario_id: UUID = None, instituicao_id: UUID = None, institution_id: str = Depends(verify_token)):
    try:
        resposta = listar_chaves_pix_service(usuario_id, instituicao_id)
        return resposta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar as chaves PIX: {e}")
    
@router.get("/chave_pix/find/")
async def buscar_dados_por_chave(chave: str, institution_id: str = Depends(verify_token)):
    try:
        resposta = buscar_dados_por_chave_service(chave)
        if not resposta:
            raise HTTPException(status_code=404, detail="Chave PIX não encontrada")
        return resposta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados pela chave PIX: {e}")

@router.post("/usuario/")
async def criar_usuario(usuario: UsuarioCreate, institution_id: str = Depends(verify_token)):
    try:  
        resposta = criar_usuario_service(usuario)
        return resposta

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar o usuário: {e}")

@router.delete("/usuario/{usuario_id}")
async def apagar_usuario(usuario_id: UUID, institution_id: str = Depends(verify_token)):
    try:
        resposta = apagar_usuario_service(usuario_id)
        return resposta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao apagar o usuário: {e}")

@router.get("/usuario/{usuario_id}")
async def retornar_usuario(usuario_id: UUID, institution_id: str = Depends(verify_token)):
    try:
        resposta = retornar_usuario_service(usuario_id)
        return resposta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao retornar o usuário: {e}")

@router.get("/usuario/")
async def listar_usuarios(instituicao_id: UUID = None, institution_id: str = Depends(verify_token)):
    try:
        resposta = listar_usuarios_service(instituicao_id)
        return resposta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar os usuários: {e}")
    
@router.get("/usuario/find/")
async def buscar_usuario_por_cpf(cpf: str, institution_id: str = Depends(verify_token)):
    try:
        resposta = buscar_usuario_por_cpf_service(cpf)
        if not resposta:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        return resposta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar o usuário pelo CPF: {e}")
