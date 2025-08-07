from fastapi import APIRouter, HTTPException, Query

from ..models.models import Funcionario, Usuario
from ..models.db_setup import conexao_bd
from ..schemas.funcionario import (
    FuncionarioEdit,
    FuncionarioOut,
    FuncionarioIn,
    tipoFuncionarioEnum,
)
from ..utils.permissoes import requer_permissao
from pydantic import EmailStr
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import aliased
from validate_docbr import CPF  # type: ignore

cpf = CPF()

funcionarios_router = APIRouter(prefix="/funcionario", tags=["Funcionário"])
router = funcionarios_router


def valida_e_retorna_cpf(funcionario_cpf: str):
    funcionario_cpf = funcionario_cpf.replace(".", "").replace("-", "")

    if not cpf.validate(funcionario_cpf):
        raise HTTPException(status_code=400, detail="CPF inválido")

    return funcionario_cpf


def valida_funcionario(funcionario: FuncionarioIn, db: conexao_bd):
    funcionario.cpf = valida_e_retorna_cpf(funcionario.cpf)

    if funcionario.cpf in db.scalars(select(Funcionario.cpf)):
        raise HTTPException(status_code=409, detail="CPF já cadastrado no sistema")

    if funcionario.email in db.scalars(select(Funcionario.email)):
        raise HTTPException(status_code=409, detail="Email já cadastrado no sistema")

    return funcionario


@router.post(
    "/",
    summary="Cria um funcionário no sistema",
    tags=["Funcionário"],
    dependencies=[requer_permissao("admin")],
)
def cadastra_funcionario(funcionario: FuncionarioIn, db: conexao_bd):
    funcionario = valida_funcionario(funcionario, db)

    usuario = Funcionario(
        cpf=funcionario.cpf,
        nome=funcionario.nome,
        senha=funcionario.senha,
        email=funcionario.email,
        tipo=funcionario.tipo.lower(),
        data_entrada=date.today(),
    )

    db.add(usuario)
    return {"message": "Funcionário cadastrado com sucesso"}


@router.put(
    "/{id}/",
    response_model=FuncionarioOut,
    summary="Atualiza os dados de um funcionário",
    tags=["Funcionário"],
    dependencies=[requer_permissao("admin")],
)
def atualiza_funcionario(id: int, funcionario: FuncionarioEdit, db: conexao_bd):
    funcionarioExistente = db.scalar(select(Funcionario).where(Funcionario.id == id))

    if not funcionarioExistente:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")

    for campo, valor in funcionario.model_dump(exclude_unset=True).items():
        setattr(funcionarioExistente, campo, valor)

    db.commit()
    db.refresh(funcionarioExistente)
    return funcionarioExistente


@router.get(
    "/",
    summary="Retorna todos os funcionários cadastrados",
    tags=["Funcionário"],
    response_model=list[FuncionarioOut],
)
def busca_funcionarios(
    db: conexao_bd,
    id: int | None = Query(None, description="Filtra pelo id do funcionário"),
    cpf: str | None = Query(None, description="Filtra pelo cpf do funcionário"),
    nome: str | None = Query(None, description="Filtra pelo nome do funcionário"),
    email: EmailStr | None = Query(
        None, description="Filtra pelo email do funcionário"
    ),
    tipo: tipoFuncionarioEnum | None = Query(
        None, description="Filtra pelo tipo do funcionário"
    ),
    data_entrada: date | None = Query(
        None, description="Filtra pela data de entrada do funcionário"
    ),
    data_saida: date | None = Query(
        None, description="Filtra pela data de saida do funcionário"
    ),
):
    usuario_alias = aliased(Usuario)
    query = select(Funcionario).join(
        usuario_alias, Funcionario.usuario_id == usuario_alias.id
    )

    if id:
        query = query.where(usuario_alias.id == id)

    if cpf:
        query = query.where(usuario_alias.cpf == cpf)

    if nome:
        query = query.where(Usuario.nome.ilike(f"%{nome}%"))

    if tipo:
        query = query.where(Funcionario.tipo == tipo)

    if email:
        query = query.where(Funcionario.email == email)

    if data_entrada:
        query = query.where(Funcionario.data_entrada == data_entrada)

    if data_saida:
        query = query.where(Funcionario.data_saida == data_saida)

    usuarios = db.scalars(query).all()
    return usuarios


@router.delete(
    "/",
    summary="Remove um funcionário pelo CPF",
    tags=["Funcionário"],
    dependencies=[requer_permissao("admin")],
)
def deleta_funcionario(db: conexao_bd, cpf: str):
    cpf = valida_e_retorna_cpf(cpf)
    funcionario = db.scalar(select(Funcionario).where(Funcionario.cpf == cpf))
    if not funcionario:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")

    db.delete(funcionario)
    db.commit()
    return {"message": "Funcionário deletado com sucesso"}


@router.post(
    "/{cpf}/desativar",
    summary="Desativa um funcionário pelo CPF (LGPD)",
    tags=["Funcionário"],
    dependencies=[requer_permissao("admin")],
)
def desativa_funcionario(db: conexao_bd, cpf: str, data_saida: date):
    cpf = valida_e_retorna_cpf(cpf)

    usuario_alias = aliased(Usuario)
    funcionario = db.scalar(
        select(Funcionario)
        .join(usuario_alias, Funcionario.usuario_id == usuario_alias.id)
        .where(usuario_alias.cpf == cpf)
    )
    if not funcionario:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")

    if funcionario.data_saida is not None:
        raise HTTPException(status_code=400, detail="Funcionário já foi desativado")

    funcionario.email = None
    funcionario.data_saida = data_saida
    db.commit()

    return {"message": "Funcionário desativado com sucesso"}
