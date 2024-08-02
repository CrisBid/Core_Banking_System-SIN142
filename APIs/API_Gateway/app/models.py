from pydantic import BaseModel

class TransacaoRequest(BaseModel):
    chave_pix: str
    valor: float

class AuthRequest(BaseModel):
    client_id: str
    client_secret: str

class AtualizaChavePix(BaseModel):
    usuario_id: str
    chave_pix: str

