from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from ..models.models import Funcionario
from ..models.db_setup import conexao_bd
from ..schemas.auth import LoginDTO
from ..core.seguranca import gerar_hash, verificar_hash, cria_token_de_acesso
from ..utils.validacao import valida_e_retorna_cpf

auth_router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"],
)
router = auth_router


def get_usuario_por_cpf(db: conexao_bd, cpf: str):
    cpf = valida_e_retorna_cpf(cpf)
    usuario = db.scalar(
        select(Funcionario).where(Funcionario.cpf_hash == gerar_hash(cpf))
    )
    return usuario


@router.post(
    "/login",
    summary="Realiza autenticação do usuário no sistema",
    tags=["Autenticação"],
)
async def login(login_data: LoginDTO, db: conexao_bd):
    usuario = get_usuario_por_cpf(db, login_data.cpf)

    if (
        usuario
        and verificar_hash(login_data.senha, usuario.senha)
        and usuario.data_saida is None
    ):
        token = cria_token_de_acesso(
            {"sub": usuario.cpf, "tipo": usuario.tipo.value, "id": usuario.id}
        )
        return {"token": token, "tipo": usuario.tipo.value}

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário ou senha incorretos",
        )
