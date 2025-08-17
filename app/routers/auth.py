from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from ..models.models import Funcionario
from ..models.db_setup import conexao_bd
from ..schemas.auth import LoginDTO
from ..core.seguranca import verificar_hash, cria_token_de_acesso

auth_router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"],
)
router = auth_router


def get_usuario_por_cpf(db: conexao_bd, cpf: str):
    cpf = cpf.replace(".", "").replace("-", "")
    usuario = db.scalar(select(Funcionario).where(Funcionario.cpf == cpf))
    return usuario


@router.post(
    "/login",
    summary="Realiza autenticação do usuário no sistema",
    tags=["Autenticação"],
)
async def login(login_data: LoginDTO, db: conexao_bd):
    usuario = get_usuario_por_cpf(db, login_data.cpf)

    if usuario and verificar_hash(login_data.senha, usuario.senha):
        token = cria_token_de_acesso({"sub": usuario.cpf, "tipo": usuario.tipo.value})
        return {"token": token}

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário ou senha incorretos")
