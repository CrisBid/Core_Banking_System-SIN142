from fastapi import APIRouter, Request, Depends
from app.services import publish_to_queue, validate_with_auth_service, update_db_service
from app.models import TransacaoRequest, AuthRequest, AtualizaChavePix
from app.auth import verify_token  # Importe a função de verificação de token

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

@router.post("/atualiza_chave/")
async def atualiza_chave(atualiza_chave_pix: AtualizaChavePix, institution_id: str = Depends(verify_token)):
    # Validação do token já ocorreu, se chegou aqui, o token é válido
    response = await update_db_service(atualiza_chave_pix)
    return response
