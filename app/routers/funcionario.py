from fastapi import APIRouter

from ..models.models import Funcionario
from ..models.db_setup import conexao_bd
from ..schemas.funcionario import FuncionarioOut

from sqlalchemy import select

funcionarios_router = APIRouter(
    prefix="/funcionario",
    tags=["Funcionário"],
)
router = funcionarios_router


# Sempre preencham summary e tags
# Tags fazem sentido de ir nos APIRouter tmb
@router.post(
    "/{cpf}/{nome}",
    summary="Cria um funcionário",
)
def funcionario(cpf: str, nome: str, db: conexao_bd):
    """
    Imaginem que eu fiz um 'FuncionarioIn'
    """
    usuario = Funcionario(cpf=cpf, nome=nome, senha="a", email="a", tipo="admin")
    db.add(usuario)
    return {"message": "Funcionário criado com sucesso"}


@router.get(
    "/",
    summary="Pega todos os funcionários",
    tags=["Funcionário"],
    response_model=list[FuncionarioOut],
)
def funcionarios(db: conexao_bd):
    usuarios = db.scalars(select(Funcionario)).all()
    return usuarios
