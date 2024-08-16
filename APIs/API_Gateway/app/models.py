from pydantic import BaseModel

class TransacaoRequest(BaseModel):
    chave_pix: str
    valor: float

class AuthRequest(BaseModel):
    instituicao_id: str
    instituicao_secret: str

class AtualizaChavePix(BaseModel):
    usuario_id: str
    chave_pix: str

