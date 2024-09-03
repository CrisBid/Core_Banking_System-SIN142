from pydantic import BaseModel

class TransacaoRequest(BaseModel):
    chave_pix: str
    valor: float

class Transacao(BaseModel):
    usuario_origem: str
    usuario_destino: str
    instituicao_origem: str
    instituicao_destino: str
    chave_pix: str
    tipo_chave: str
    valor: float

