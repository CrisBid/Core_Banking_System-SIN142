from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import Optional

class ChavePixRequest(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    chave_pix: str
    tipo_chave: str  # Ex: 'cpf', 'email', 'telefone'
    instituicao_id: UUID
    usuario_id: UUID

class ChavePix(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    chave_pix: str
    tipo_chave: str  # Ex: 'cpf', 'email', 'telefone'
    usuario_id: UUID
    instituicao_id: UUID
    created_at: str

class TransacaoRequest(BaseModel):
    institution_id: str
    usuario_id: str
    chave: str
    tipo_chave: str
    valor: float

