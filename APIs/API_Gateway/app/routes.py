from fastapi import APIRouter, Request, HTTPException, Depends
from app.services import authenticate_request, publish_to_queue, validate_with_auth_service, update_db_service
from app.models import TransacaoRequest, AuthRequest, AtualizaChavePix

router = APIRouter()

@router.post("/transacao/")
async def criar_transacao(request: Request, transacao_request: TransacaoRequest, token: str):
    await authenticate_request(token)
    await publish_to_queue(transacao_request, 'transacoes')
    return {"status": "Transação encaminhada"}

@router.post("/auth/")
async def autenticar(auth_request: AuthRequest):
    response = await validate_with_auth_service(auth_request)
    return response

@router.post("/atualiza_chave/")
async def atualiza_chave(atualiza_chave_pix: AtualizaChavePix):
    response = await update_db_service(atualiza_chave_pix)
    return response

