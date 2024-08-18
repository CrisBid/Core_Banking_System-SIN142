from pydantic import BaseModel
from uuid import UUID

class AuthRequest(BaseModel):
    institution_id: str
    institution_secret: str

class Instituicao(BaseModel):
    instituicao_id: UUID
    nome: str
    codigo: str

class Usuario(BaseModel):
    usuario_id: UUID
    chave_pix: str
    tipo_chave: str
    instituicao_id: UUID
    nome: str
    email: str
    cpf: str
    telefone: str

