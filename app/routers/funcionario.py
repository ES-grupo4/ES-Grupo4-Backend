from fastapi import APIRouter, HTTPException

from ..models.models import Funcionario
from ..models.db_setup import conexao_bd
from ..schemas.funcionario import FuncionarioOut, FuncionarioIn
from ..utils.permissoes import requer_permissao

from sqlalchemy import select
from validate_docbr import CPF
from email_validator import validate_email, EmailNotValidError

cpf = CPF()

funcionarios_router = APIRouter(prefix="/funcionario", tags=["Funcionário"])
router = funcionarios_router


# Sempre preencham summary e tags
# Tags fazem sentido de ir nos APIRouter tmb
# TODO: Rota de criar funcionário:
#   - Verificar se o funcionário existe antes de tudo
#   - Se existir solta um erro, se não, insere

# NOTE: colocar verificação se é post ou put, se for post verifica se o email e o cpf ja foram cadastrados
def valida_funcionario(funcionario: FuncionarioIn, db: conexao_bd):
    funcionario.cpf = funcionario.cpf.replace(".", "").replace("-", "")

    if not cpf.validate(funcionario.cpf):
        raise HTTPException(status_code=400, detail="CPF inválido")

    if funcionario.cpf in db.scalars(select(Funcionario.cpf)):
        raise HTTPException(status_code=409, detail="CPF já cadastrado no sistema")

    if not validate_email(funcionario.email):
        raise HTTPException(status_code=400, detail="Email inválido")

    if funcionario.email in db.scalars(select(Funcionario.email)):
        raise HTTPException(status_code=409, detail="Email já cadastrado no sistema")
    
    if funcionario.tipo.lower() not in ("admin", "funcionario", "funcionário"):
        raise HTTPException(status_code=400, detail="Tipo de funcionário inválido")

    if funcionario.tipo.lower() == "funcionário":
        funcionario.tipo = "funcionario"

    return funcionario


@router.post(
    "/",
    summary="Cria um funcionário no sistema",
    # dependencies=[requer_permissao("admin")],
)
def cadastra_funcionario(funcionario: FuncionarioIn, db: conexao_bd):
    funcionario = valida_funcionario(funcionario, db)

    # NOTE: fazer hash de cpf, senha e
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


@router.put(
    "/{id}/",
    response_model=FuncionarioOut,
    summary="Atualiza os dados de um funcionário",
    tags=["Funcionário"],
    dependencies=[requer_permissao("admin")],
)
def atualiza_funcionario(
    funcionario_id: int, funcionario: FuncionarioIn, db: conexao_bd
):
    funcionarioExistente = db.scalar(
        select(Funcionario).where(Funcionario.id == funcionario_id)
    )
    if not funcionarioExistente:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if not cpf.validate(funcionario.cpf):
        raise HTTPException(status_code=400, detail="CPF inválido")

    update_dict = funcionario.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(funcionarioExistente, key, value)

    db.commit()
    db.refresh(funcionarioExistente)
    return funcionarioExistente


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
