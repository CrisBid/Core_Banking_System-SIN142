from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import Optional

class Usuario(BaseModel):
    usuario_id: UUID = Field(default_factory=uuid4)
    nome: str
    email: str
    cpf: str
    telefone: str
    created_at: str

class UsuarioCreate(BaseModel):
    nome: str
    email: str
    cpf: str
    telefone: str

