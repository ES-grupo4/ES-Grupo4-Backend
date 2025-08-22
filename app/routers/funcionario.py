from fastapi import APIRouter, HTTPException, Query

from ..models.models import Funcionario
from ..models.db_setup import conexao_bd
from ..schemas.funcionario import (
    FuncionarioEdit,
    FuncionarioOut,
    FuncionarioIn,
    tipoFuncionarioEnum,
)
from ..utils.permissoes import requer_permissao
from ..utils.validacao import valida_e_retorna_cpf
from pydantic import EmailStr
from datetime import date

from sqlalchemy import select
from validate_docbr import CPF  # type: ignore

cpf = CPF()

funcionarios_router = APIRouter(prefix="/funcionario", tags=["Funcionário"])
router = funcionarios_router


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
    query = select(Funcionario)

    if id:
        query = query.where(Funcionario.id == id)

    if cpf:
        query = query.where(Funcionario.cpf == cpf)

    if nome:
        query = query.where(Funcionario.nome.ilike(f"%{nome}%"))

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


@router.get(
    "/admin/",
    summary="Retorna todos os administradores cadastrados",
    tags=["Funcionário"],
    response_model=list[FuncionarioOut],
)
def busca_admins(
    db: conexao_bd,
    id: int | None = Query(None, description="Filtra pelo id do admin"),
    cpf: str | None = Query(None, description="Filtra pelo cpf do admin"),
    nome: str | None = Query(None, description="Filtra pelo nome do admin"),
    email: EmailStr | None = Query(None, description="Filtra pelo email do admin"),
    tipo: tipoFuncionarioEnum | None = Query(
        None, description="Filtra pelo tipo do admin"
    ),
    data_entrada: date | None = Query(
        None, description="Filtra pela data de entrada do admin"
    ),
    data_saida: date | None = Query(
        None, description="Filtra pela data de saida do admin"
    ),
):
    query = select(Funcionario).where(Funcionario.tipo == "admin")

    if id:
        query = query.where(Funcionario.id == id)

    if cpf:
        query = query.where(Funcionario.cpf == cpf)

    if nome:
        query = query.where(Funcionario.nome.ilike(f"%{nome}%"))

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

    funcionario = db.scalar(select(Funcionario).where(Funcionario.cpf == cpf))
    if not funcionario:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")

    if funcionario.data_saida is not None:
        raise HTTPException(status_code=400, detail="Funcionário já foi desativado")

    funcionario.email = None
    funcionario.data_saida = data_saida
    db.commit()

    return {"message": "Funcionário desativado com sucesso"}
