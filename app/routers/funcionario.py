from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func
from math import ceil
from pydantic import EmailStr
from datetime import date

from ..models.models import Funcionario, FuncionarioTipo
from ..models.db_setup import conexao_bd
from ..schemas.funcionario import (
    FuncionarioEdit,
    FuncionarioOut,
    FuncionarioIn,
    tipoFuncionarioEnum,
    FuncionarioPaginationOut,
)
from ..core.permissoes import requer_permissao
from ..utils.validacao import valida_e_retorna_cpf
from ..core.seguranca import gerar_hash, criptografa_cpf
from validate_docbr import CPF  # type: ignore

cpf = CPF()

funcionarios_router = APIRouter(prefix="/funcionario", tags=["Funcionário"])
router = funcionarios_router


def valida_funcionario(funcionario: FuncionarioIn, db: conexao_bd):
    funcionario.cpf = valida_e_retorna_cpf(funcionario.cpf)

    if gerar_hash(funcionario.cpf) in db.scalars(select(Funcionario.cpf_hash)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="CPF já cadastrado no sistema"
        )

    if funcionario.email in db.scalars(select(Funcionario.email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email já cadastrado no sistema",
        )

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
        cpf_cript=criptografa_cpf(funcionario.cpf),
        cpf_hash=gerar_hash(funcionario.cpf),
        nome=funcionario.nome,
        senha=gerar_hash(funcionario.senha),
        email=funcionario.email,
        tipo=FuncionarioTipo(funcionario.tipo),
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
    funcionario_existente = db.scalar(select(Funcionario).where(Funcionario.id == id))

    if not funcionario_existente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Funcionário não encontrado"
        )

    for campo, valor in funcionario.model_dump(exclude_unset=True).items():
        if campo == "cpf":
            valor = valida_e_retorna_cpf(valor)
            funcionario_existente.cpf_cript = criptografa_cpf(valor)
            funcionario_existente.cpf_hash = gerar_hash(valor)
        setattr(funcionario_existente, campo, valor)

    db.commit()
    db.refresh(funcionario_existente)
    return funcionario_existente


@router.get(
    "/",
    summary="Retorna todos os funcionários cadastrados",
    tags=["Funcionário"],
    response_model=FuncionarioPaginationOut,
    dependencies=[requer_permissao("funcionario", "admin")],
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
        None, description="Filtra pela data de saída do funcionário"
    ),
    page: int = Query(1, ge=1, description="Número da página (padrão 1)"),
    page_size: int = Query(
        10, ge=1, le=100, description="Quantidade de registros por página (padrão 10)"
    ),
):
    query = select(Funcionario)

    if id:
        query = query.where(Funcionario.id == id)
    if cpf:
        query = query.where(Funcionario.cpf_hash == gerar_hash(cpf))
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

    offset = (page - 1) * page_size
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    funcionarios_na_pagina = db.scalars(query.offset(offset).limit(page_size)).all()
    funcionarios_out = [FuncionarioOut.from_orm(f) for f in funcionarios_na_pagina]

    return {
        "total_in_page": len(funcionarios_out),
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size) if total else 0,
        "items": funcionarios_out,
    }


@router.delete(
    "/",
    summary="Remove um funcionário pelo CPF",
    tags=["Funcionário"],
    dependencies=[requer_permissao("admin")],
)
def deleta_funcionario(db: conexao_bd, cpf: str):
    cpf = valida_e_retorna_cpf(cpf)
    funcionario = db.scalar(
        select(Funcionario).where(Funcionario.cpf_hash == gerar_hash(cpf))
    )
    if not funcionario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Funcionário não encontrado"
        )

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

    funcionario = db.scalar(
        select(Funcionario).where(Funcionario.cpf_hash == gerar_hash(cpf))
    )
    if not funcionario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Funcionário não encontrado"
        )

    if funcionario.data_saida is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Funcionário já foi desativado",
        )

    funcionario.email = None
    funcionario.data_saida = data_saida
    db.commit()

    return {"message": "Funcionário desativado com sucesso"}
