from pydantic import BaseModel

class TransacaoRequest(BaseModel):
    chave_pix: str
    valor: float

class AuthRequest(BaseModel):
    instituicao_id: str
    instituicao_secret: str

class ChavePixRequest(BaseModel):
    chave_pix: str
    tipo_chave: str  # Ex: 'cpf', 'email', 'telefone'
    usuario_id: str
    instituicao_id: str

class Usuario(BaseModel):
    usuario_id: str
    nome: str
    email: str
    cpf: str
    telefone: str

class UsuarioCreate(BaseModel):
    nome: str
    email: str
    cpf: str
    telefone: str
