from uuid import UUID
from app.models import Usuario, UsuarioCreate
from app.database import get_cassandra_session

def criar_usuario(usuario: Usuario) -> Usuario:
    try:
        session = get_cassandra_session()
        
        query = """
        INSERT INTO usuarios (usuario_id, nome, email, cpf, telefone, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        session.execute(query, (
            usuario.usuario_id,
            usuario.nome,
            usuario.email,
            usuario.cpf,
            usuario.telefone,
            usuario.created_at,
        ))

        # Retorna o objeto do usuário criado
        return usuario
    
    except Exception as e:
        print(f"Erro ao criar usuário: {e}")
        raise

def apagar_usuario(usuario_id: UUID) -> Usuario:
    session = get_cassandra_session()

    # Busca o usuário antes de excluí-lo
    query_select = "SELECT usuario_id, nome, email, cpf, telefone, created_at FROM usuarios WHERE usuario_id = %s"
    row = session.execute(query_select, (usuario_id,)).one()

    if row:
        usuario = Usuario(
            usuario_id=row.usuario_id,
            nome=row.nome,
            email=row.email,
            cpf=row.cpf,
            telefone=row.telefone,
            created_at=str(row.created_at)
        )

        # Exclui o usuário
        query_delete = "DELETE FROM usuarios WHERE usuario_id = %s"
        session.execute(query_delete, (usuario_id,))

        # Retorna o objeto do usuário excluído
        return usuario
    else:
        raise ValueError(f"Usuário com ID {usuario_id} não encontrado.")


def retornar_usuario(usuario_id: UUID):
    session = get_cassandra_session()
    
    query = "SELECT usuario_id, nome, email, cpf, telefone, created_at FROM usuarios WHERE usuario_id = %s"
    row = session.execute(query, (usuario_id,)).one()

    if row:
        return Usuario(
            usuario_id=str(row.usuario_id),
            nome=row.nome,
            email=row.email,
            cpf=row.cpf,
            telefone=row.telefone,
            created_at=str(row.created_at)
        )
    else:
        return None

def listar_usuarios():
    session = get_cassandra_session()

    query = "SELECT usuario_id, nome, email, cpf, telefone, created_at FROM usuarios"
    rows = session.execute(query)

    usuarios = []
    for row in rows:
        usuarios.append(Usuario(
            usuario_id=str(row.usuario_id),
            nome=row.nome,
            email=row.email,
            cpf=row.cpf,
            telefone=row.telefone,
            created_at=str(row.created_at)
        ))

    return usuarios

def retornar_usuario_por_cpf(cpf: str):
    session = get_cassandra_session()

    query = "SELECT usuario_id, nome, email, cpf, telefone, created_at FROM usuarios WHERE cpf = %s"
    row = session.execute(query, (cpf,)).one()

    if row:
        return Usuario(
            usuario_id=str(row.usuario_id),
            nome=row.nome,
            email=row.email,
            cpf=row.cpf,
            telefone=row.telefone,
            created_at=str(row.created_at)
        )
    else:
        return None

