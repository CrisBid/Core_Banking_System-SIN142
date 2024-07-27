from pydantic import BaseModel

class TransacaoRequest(BaseModel):
    chave_pix: str
    valor: float

