from fastapi import APIRouter, HTTPException

from ..models.models import Funcionario
from ..models.db_setup import conexao_bd
from ..schemas.funcionario import FuncionarioOut, FuncionarioIn
from ..utils.permissoes import requer_permissao

from sqlalchemy import select
from validate_docbr import CPF

cpf = CPF()

funcionarios_router = APIRouter(prefix="/funcionario", tags=["Funcionário"])
router = funcionarios_router


# Sempre preencham summary e tags
# Tags fazem sentido de ir nos APIRouter tmb
# TODO: Rota de criar funcionário:
#   - Verificar se o funcionário existe antes de tudo
#   - Se existir solta um erro, se não, insere
@router.post(
    "/",
    summary="Cria um funcionário no sistema",
    dependencies=[requer_permissao("admin")],
)
def funcionario(funcionario: FuncionarioIn, db: conexao_bd):
    if funcionario.cpf in db.scalars(select(Funcionario.cpf)):
        raise HTTPException(status_code=409, detail="CPF já cadastrado no sistema")

    if not cpf.validate(funcionario.cpf):
        raise HTTPException(status_code=400, detail="CPF inválido")

    if funcionario.email in db.scalars(select(Funcionario.email)):
        raise HTTPException(status_code=409, detail="Email já cadastrado no sistema")

    if funcionario.tipo.lower() not in ("admin", "funcionario", "funcionário"):
        raise HTTPException(status_code=400, detail="Tipo de funcionário inválido")

    if funcionario.tipo.lower() == "funcionário":
        funcionario.tipo = "funcionario"

    # NOTE: lembrar de ver como vai funcionar a aplicação da LGPD nos dados da galera: hash de cpf, senha, etc
    usuario = Funcionario(
        cpf=funcionario.cpf,
        nome=funcionario.nome,
        senha=funcionario.senha,
        email=funcionario.email,
        tipo=funcionario.tipo.lower(),
    )

    db.add(usuario)
    return {"message": "Funcionário cadastrado com sucesso"}

"""
TODO:
 - POST/funcionarios - Criar novo funcionário (admin route)
 - PUT/funcionarios/{id} - Atualizar dados do funcionário (admin route)
 - GET/funcionarios?{optional-filter}= - Buscar funcionários
 - POST/funcionarios/credentials - Verificar credenciais de login
 - DELETE/funcionarios/{id} - Remoção conforme LGPD (admin route)
"""
# NOTE: ver a questão dos funcionários ativos: vão ser listados ou não?
@router.get(
    "/",
    summary="Retorna todos os funcionários cadastrados",
    tags=["Funcionário"],
    response_model=list[FuncionarioOut],
)
def funcionarios(db: conexao_bd):
    usuarios = db.scalars(select(Funcionario)).all()
    return usuarios
