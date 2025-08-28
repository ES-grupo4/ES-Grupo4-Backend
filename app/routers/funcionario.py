from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_, cast, and_
from sqlalchemy.sql.sqltypes import String as SAString
from math import ceil
from pydantic import EmailStr
from datetime import date, datetime
import traceback

from app.core.historico_acoes import AcoesEnum, guarda_acao

from ..models.models import Funcionario, FuncionarioTipo
from ..models.db_setup import conexao_bd
from ..schemas.funcionario import (
    FuncionarioEdit,
    FuncionarioOut,
    FuncionarioIn,
    FuncionarioPaginationOut,
)
from ..core.permissoes import requer_permissao
from ..utils.validacao import valida_e_retorna_cpf
from ..core.seguranca import gerar_hash, criptografa_cpf
from validate_docbr import CPF  # type: ignore

cpf = CPF()

funcionarios_router = APIRouter(prefix="/funcionario", tags=["Funcionário"])
router = funcionarios_router


def valida_funcionario(
    funcionario: FuncionarioIn,
    db: conexao_bd,
):
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
)
def cadastra_funcionario(
    ator: Annotated[dict, Depends(requer_permissao("admin"))],
    funcionario: FuncionarioIn,
    db: conexao_bd,
):
    funcionario = valida_funcionario(funcionario, db)
    usuario = Funcionario(
        cpf_cript=criptografa_cpf(funcionario.cpf),
        cpf_hash=gerar_hash(funcionario.cpf),
        nome=funcionario.nome,
        senha=gerar_hash(funcionario.senha),
        email=funcionario.email,
        tipo=FuncionarioTipo(funcionario.tipo),
        data_entrada=funcionario.data_entrada,
    )

    db.add(usuario)
    db.commit()
    guarda_acao(db, AcoesEnum.CADASTRAR_FUNCIONARIO, ator["cpf"], usuario.id)
    return {"message": "Funcionário cadastrado com sucesso"}


@router.put(
    "/{id}/",
    response_model=FuncionarioOut,
    summary="Atualiza os dados de um funcionário",
)
def atualiza_funcionario(
    ator: Annotated[dict, Depends(requer_permissao("admin"))],
    id: int,
    funcionario: FuncionarioEdit,
    db: conexao_bd,
):
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

    guarda_acao(
        db, AcoesEnum.ATUALIZAR_FUNCIONARIO, ator["cpf"], funcionario_existente.id
    )
    return funcionario_existente


@router.get(
    "/",
    summary="Retorna todos os funcionários cadastrados",
    response_model=FuncionarioPaginationOut,
    dependencies=[Depends(requer_permissao("funcionario", "admin"))],
)
def busca_funcionarios(
    db: conexao_bd,
    id: int | None = Query(None, description="Filtra pelo id do funcionário"),
    cpf: str | None = Query(None, description="Filtra pelo cpf do funcionário"),
    nome: str | None = Query(None, description="Filtra pelo nome do funcionário"),
    email: EmailStr | None = Query(
        None, description="Filtra pelo email do funcionário"
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
    query = select(Funcionario).where(cast(Funcionario.tipo, SAString) == "funcionario")

    if id:
        query = query.where(Funcionario.id == id)
    if cpf:
        query = query.where(Funcionario.cpf_hash == gerar_hash(cpf))
    if nome:
        query = query.where(Funcionario.nome.ilike(f"%{nome}%"))
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


@router.get(
    "/admins",
    summary="Pesquisa paginada de funcionários/admins (uma string aplicada a várias colunas)",
    response_model=FuncionarioPaginationOut,
    dependencies=[Depends(requer_permissao("funcionario", "admin"))],
)
def pesquisar_funcionarios(
    db: conexao_bd,
    busca: str | None = Query(
        default=None,
        description=(
            "String de busca aplicada a id, nome, CPF (se for CPF válido), email, tipo e datas"
        ),
    ),
    desativados: bool | None = Query(
        None, description="Filtra pelos funcionários/admins desativados"
    ),
    anonimizados: bool | None = Query(
        None, description="Filtra pelos funcionários/admins anonimizados"
    ),
    page: int = Query(1, ge=1, description="Número da página (padrão 1)"),
    page_size: int = Query(
        10, ge=1, le=100, description="Quantidade de registros por página"
    ),
):
    query = select(Funcionario)

    if busca:
        busca_like = f"%{busca}%"
        conditions = []

        conditions.append(Funcionario.nome.ilike(busca_like))
        conditions.append(Funcionario.email.ilike(busca_like))
        conditions.append(cast(Funcionario.tipo, SAString).ilike(busca_like))

        if busca.isdigit():
            conditions.append(Funcionario.id == int(busca))

        try:
            cpf_norm = valida_e_retorna_cpf(busca)
            conditions.append(Funcionario.cpf_hash == gerar_hash(cpf_norm))
        except Exception:
            traceback.print_exc()
            pass

        parsed_date = None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                parsed_date = datetime.strptime(busca, fmt).date()
                break
            except Exception:
                continue
        if parsed_date:
            conditions.append(Funcionario.data_entrada == parsed_date)
            conditions.append(Funcionario.data_saida == parsed_date)

        query = query.where(or_(*conditions))

    if desativados is True:
        query = query.where(Funcionario.data_saida.is_not(None))

    if anonimizados is True:
        query = query.where(
            and_(Funcionario.nome.is_(None), Funcionario.cpf_hash.is_(None))
        )
    else:
        # Excluir registros anonimizados por padrão
        query = query.where(
            ~and_(Funcionario.nome.is_(None), Funcionario.cpf_hash.is_(None))
        )

    offset = (page - 1) * page_size
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    resultados = db.scalars(query.offset(offset).limit(page_size)).all()
    items = [FuncionarioOut.from_orm(f) for f in resultados]

    return {
        "total_in_page": len(resultados),
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size) if total else 0,
        "items": items,
    }


@router.get(
    "/admin/",
    summary="Retorna todos os administradores cadastrados",
    response_model=FuncionarioPaginationOut,
    dependencies=[Depends(requer_permissao("funcionario", "admin"))],
)
def busca_admins(
    db: conexao_bd,
    id: int | None = Query(None, description="Filtra pelo id do funcionário"),
    cpf: str | None = Query(None, description="Filtra pelo cpf do funcionário"),
    nome: str | None = Query(None, description="Filtra pelo nome do funcionário"),
    email: EmailStr | None = Query(
        None, description="Filtra pelo email do funcionário"
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
    query = select(Funcionario).where(cast(Funcionario.tipo, SAString) == "admin")

    if id:
        query = query.where(Funcionario.id == id)
    if cpf:
        query = query.where(Funcionario.cpf_hash == gerar_hash(cpf))
    if nome:
        query = query.where(Funcionario.nome.ilike(f"%{nome}%"))
    if email:
        query = query.where(Funcionario.email == email)
    if data_entrada:
        query = query.where(Funcionario.data_entrada == data_entrada)
    if data_saida is not None:
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
)
def deleta_funcionario(
    ator: Annotated[dict, Depends(requer_permissao("admin"))], db: conexao_bd, cpf: str
):
    cpf = valida_e_retorna_cpf(cpf)
    funcionario = db.scalar(
        select(Funcionario).where(Funcionario.cpf_hash == gerar_hash(cpf))
    )
    if not funcionario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Funcionário não encontrado"
        )

    db.delete(funcionario)
    guarda_acao(db, AcoesEnum.DELETAR_FUNCIONARIO, ator["cpf"], funcionario.id)
    return {"message": "Funcionário deletado com sucesso"}


@router.post(
    "/{cpf}/desativar",
    summary="Desativa um funcionário pelo CPF (LGPD)",
)
def desativa_funcionario(
    ator: Annotated[dict, Depends(requer_permissao("admin"))],
    db: conexao_bd,
    cpf: str,
    data_saida: date,
):
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

    db.flush()
    guarda_acao(db, AcoesEnum.DESATIVAR_FUNCIONARIO, ator["cpf"], funcionario.id)

    return {"message": "Funcionário desativado com sucesso"}


@router.post(
    "/{id}/anonimizar",
    summary="Anonimiza um funcionário pelo ID (LGPD)",
)
def anonimiza_funcionario(
    ator: Annotated[dict, Depends(requer_permissao("admin"))], db: conexao_bd, id: int
):
    funcionario = db.scalar(select(Funcionario).where(Funcionario.id == id))
    if not funcionario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Funcionário não encontrado"
        )

    if funcionario.nome is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Funcionário já foi anonimizado",
        )

    funcionario.cpf_hash = None
    funcionario.cpf_cript = None
    funcionario.nome = None
    funcionario.email = None

    db.flush()
    guarda_acao(db, AcoesEnum.ANONIMIZAR_FUNCIONARIO, ator["cpf"], funcionario.id)

    return {"message": "Funcionário desativado com sucesso"}
