import io
from math import ceil
from typing import Annotated
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
import polars as pl

from app.core.historico_acoes import AcoesEnum, guarda_acao
from ..models.db_setup import conexao_bd
from ..models.models import Cliente
from ..core.seguranca import gerar_hash, criptografa_cpf
from ..core.permissoes import requer_permissao
from ..schemas.cliente import (
    ClienteEdit,
    ClienteIn,
    ClienteOut,
    ClienteEnum,
    ClientePaginationOut,
)
from ..utils.validacao import valida_e_retorna_cpf

cliente_router = APIRouter(
    prefix="/cliente",
    tags=["Cliente"],
)


@cliente_router.post(
    "/",
    summary="Cria um cliente",
    response_model=ClienteOut,
    status_code=status.HTTP_201_CREATED,
)
def cria_cliente(
    cliente: ClienteIn,
    ator: Annotated[dict, Depends(requer_permissao("funcionario", "admin"))],
    db: conexao_bd,
):
    """
    Cria um cliente no sistema.
    """
    cliente.cpf = valida_e_retorna_cpf(cliente.cpf)
    novo = Cliente(
        cpf_cript=criptografa_cpf(cliente.cpf),
        cpf_hash=gerar_hash(cliente.cpf),
        nome=cliente.nome,
        matricula=cliente.matricula,
        tipo=cliente.tipo,
        graduando=cliente.graduando,
        pos_graduando=cliente.pos_graduando,
        bolsista=cliente.bolsista,
    )
    db.add(novo)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cliente com esse CPF já existe.",
        )
    # db.refresh(novo)
    guarda_acao(db, AcoesEnum.CADASTRAR_CLIENTE, ator["cpf"], novo.id)
    return ClienteOut.from_orm(novo)


@cliente_router.get(
    "/",
    summary="Pega todos os clientes (com filtros opcionais)",
    response_model=ClientePaginationOut,
    dependencies=[Depends(requer_permissao("funcionario", "admin"))],
)
def listar_clientes(
    db: conexao_bd,
    nome: str | None = Query(
        default=None, description="Filtrar por nome (parcial, case-insensitive)"
    ),
    cpf: str | None = Query(
        default=None, description="Filtrar por cpf (parcial, case-insensitive)"
    ),
    matricula: str | None = Query(
        default=None, description="Filtrar por matrícula exata"
    ),
    tipo: ClienteEnum | None = Query(default=None, description="Filtrar por tipo"),
    graduando: bool | None = Query(
        default=None, description="Filtrar por quem é graduando"
    ),
    pos_graduando: bool | None = Query(
        default=None, description="Filtrar por quem é pós-graduando"
    ),
    bolsista: bool | None = Query(
        default=None, description="Filtrar por quem é bolsista"
    ),
    page: int = Query(1, ge=1, description="Número da página (padrão 1)"),
    page_size: int = Query(
        10, ge=1, le=100, description="Quantidade de clientes por página (padrão 10)"
    ),
):
    """
    Lista todos os clientes cadastrados, com possibilidade de filtros por:
    - nome (ilike %nome%)
    - matrícula (igual)
    - tipo
    - graduando
    - pos_graduando
    - bolsista

    Todos os parâmetros são opcionais e podem ser combinados.
    """
    query = select(Cliente)

    if nome is not None:
        query = query.where(Cliente.nome.ilike(f"%{nome}%"))
    if cpf is not None:
        query = query.where(Cliente.nome.ilike(f"%{gerar_hash(cpf)}%"))
    if matricula is not None:
        query = query.where(Cliente.matricula == matricula)
    if tipo is not None:
        query = query.where(Cliente.tipo == tipo)
    if graduando is not None:
        query = query.where(Cliente.graduando == graduando)
    if pos_graduando is not None:
        query = query.where(Cliente.pos_graduando == pos_graduando)
    if bolsista is not None:
        query = query.where(Cliente.bolsista == bolsista)

    offset = (page - 1) * page_size
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    clientes_na_pagina = db.scalars(query.offset(offset).limit(page_size)).all()
    clientes_out = [ClienteOut.from_orm(cliente) for cliente in clientes_na_pagina]

    return {
        "total_in_page": len(clientes_na_pagina),
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size) if total else 0,
        "items": clientes_out,
    }


@cliente_router.delete(
    "/{cpf}",
    summary="Remove um cliente pelo CPF",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remover_cliente(
    cpf: str,
    ator: Annotated[dict, Depends(requer_permissao("funcionario", "admin"))],
    db: conexao_bd,
):
    """
    Remove um cliente do sistema a partir do CPF.
    """
    cpf = valida_e_retorna_cpf(cpf)
    cliente = db.scalar(select(Cliente).where(Cliente.cpf_hash == gerar_hash(cpf)))
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado",
        )
    db.delete(cliente)
    db.flush()
    guarda_acao(db, AcoesEnum.DELETAR_CLIENTE, ator["cpf"], cliente.id)


@cliente_router.put(
    "/{cpf}",
    summary="Edita os dados de um cliente pelo CPF",
    response_model=ClienteOut,
)
def editar_cliente(
    cpf: str,
    dados: ClienteEdit,
    ator: Annotated[dict, Depends(requer_permissao("funcionario", "admin"))],
    db: conexao_bd,
):
    """
    Edita os dados de um cliente existente, exceto CPF, ID e tipo.
    """
    cpf = valida_e_retorna_cpf(cpf)
    cliente = db.scalar(select(Cliente).where(Cliente.cpf_hash == gerar_hash(cpf)))
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado",
        )
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(cliente, campo, valor)
    db.flush()
    db.refresh(cliente)
    guarda_acao(db, AcoesEnum.ATUALIZAR_CLIENTE, ator["cpf"], cliente.id)
    return ClienteOut.from_orm(cliente)


@cliente_router.put(
    "/id/{id}",
    summary="Edita os dados de um cliente pelo ID",
    response_model=ClienteOut,
)
def editar_cliente_id(
    id: int,
    dados: ClienteEdit,
    ator: Annotated[dict, Depends(requer_permissao("funcionario", "admin"))],
    db: conexao_bd,
):
    """
    Edita os dados de um cliente existente, exceto CPF, ID e tipo.
    """
    cliente = db.scalar(select(Cliente).where(Cliente.id == id))
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado",
        )
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(cliente, campo, valor)
    db.flush()
    db.refresh(cliente)
    guarda_acao(db, AcoesEnum.ATUALIZAR_CLIENTE, ator["cpf"], cliente.id)
    return ClienteOut.from_orm(cliente)


@cliente_router.get(
    "/{cpf}",
    summary="Busca um cliente pelo CPF",
    response_model=ClienteOut,
)
def buscar_cliente(cpf: str, db: conexao_bd):
    """
    Retorna os dados de um cliente a partir do CPF.
    """
    cpf = valida_e_retorna_cpf(cpf)
    cliente = db.scalar(select(Cliente).where(Cliente.cpf_hash == gerar_hash(cpf)))
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado",
        )
    return ClienteOut.from_orm(cliente)


@cliente_router.get(
    "/{id}",
    summary="Busca um cliente pelo ID",
    response_model=ClienteOut,
)
def buscar_cliente_id(id: int, db: conexao_bd):
    """
    Retorna os dados de um cliente a partir do iD.
    """
    cliente = db.scalar(select(Cliente).where(Cliente.id == id))
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado",
        )
    return ClienteOut.from_orm(cliente)


@cliente_router.delete("/{id}", summary="Anonimiza um cliente")
def anonimiza_funcionario(
    ator: Annotated[dict, Depends(requer_permissao("admin"))], db: conexao_bd, id: int
):
    cliente = db.scalar(select(Cliente).where(Cliente.id == id))
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado"
        )

    if cliente.cpf_hash is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente já foi anonimizado",
        )

    cliente.cpf_hash = None
    cliente.cpf_cript = None
    cliente.nome = None

    db.flush()
    guarda_acao(db, AcoesEnum.ANONIMIZAR_CLIENTE, ator["cpf"], cliente.id)

    return {"message": "Funcionário desativado com sucesso"}


@cliente_router.post(
    "/upload-csv/",
    summary="Cadastra clientes no sistema por meio de CSV",
)
async def upload_clientes_csv(
    db: conexao_bd,
    ator: Annotated[dict, Depends(requer_permissao("funcionario", "admin"))],
    arquivo: UploadFile = File(...),
):
    """
    Realiza a inserção em massa de clientes a partir de um arquivo CSV.
    O CSV deve conter colunas: cpf,nome,matricula,tipo,graduando,pos_graduando,bolsista
    Clientes duplicados (mesmo CPF) são ignorados.
    """
    if not arquivo.filename.endswith(".csv"):  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="O arquivo deveria ser CSV."
        )

    contents = await arquivo.read()
    try:
        tabela_csv = pl.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Erro lendo CSV: {e}"
        )

    required_columns = {
        "cpf",
        "nome",
        "matricula",
        "tipo",
        "graduando",
        "pos_graduando",
        "bolsista",
    }
    if not required_columns.issubset(set(tabela_csv.columns)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O CSV não contém as colunas necessárias.",
        )

    inseridos = 0
    clientes = []
    for linha in tabela_csv.iter_rows(named=True):
        try:
            cliente = Cliente(
                cpf_hash=gerar_hash(str(linha["cpf"])),
                cpf_cript=criptografa_cpf(str(linha["cpf"])),
                nome=str(linha["nome"]),
                matricula=str(linha["matricula"]),
                tipo=str(linha["tipo"]),
                graduando=bool(linha["graduando"]),
                pos_graduando=bool(linha["pos_graduando"]),
                bolsista=bool(linha["bolsista"]),
            )
            inseridos += 1
            clientes.append(cliente)
            db.add(cliente)
            db.flush()
        except Exception as e:
            print(f"Erro ao cadastrar {linha.get('cpf')}: {e}")
            db.rollback()
            continue
    for cliente in clientes:
        guarda_acao(
            db,
            AcoesEnum.CADASTRAR_CLIENTE,
            ator["cpf"],
            cliente.id,
        )

    return {"message": f"{inseridos} cliente(s) cadastrado(s) com sucesso."}

@cliente_router.get(
    "/search/",
    summary="Pesquisa clientes em todas as colunas",
    response_model=ClientePaginationOut,
    dependencies=[Depends(requer_permissao("funcionario", "admin"))],
)
def buscar_clientes_todos_campos(
    db: conexao_bd,
    q: str | None = Query(
        default=None, description="Termo de busca para nome, cpf, matrícula, subtipo"
    ),
    tipo: ClienteEnum | None = Query(
        default=None, description="Filtrar por tipo (externo, professor, tecnico, aluno)"
    ),
    page: int = Query(1, ge=1, description="Número da página (padrão 1)"),
    page_size: int = Query(
        10, ge=1, le=100, description="Quantidade de clientes por página (padrão 10)"
    ),
):
    """
    Pesquisa clientes em todas as colunas principais (nome, CPF, matrícula e subtipo)
    e permite filtrar adicionalmente por tipo.
    """
    query = select(Cliente)

    if q:
        like_pattern = f"%{q}%"

        # CPF precisa de tratamento especial (hash)
        cpf_hash = gerar_hash(q) if q.isdigit() else None

        filtros = [
            Cliente.nome.ilike(like_pattern),
            Cliente.matricula.ilike(like_pattern),
            Cliente.subtipo.ilike(like_pattern)
        ]
        if cpf_hash:
            filtros.append(Cliente.cpf.ilike(f"%{cpf_hash}%"))

        query = query.where(or_(*filtros))

    if tipo:
        query = query.where(Cliente.tipo == tipo)

    offset = (page - 1) * page_size
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    clientes_na_pagina = db.scalars(query.offset(offset).limit(page_size)).all()
    clientes_out = [ClienteOut.from_orm(cliente) for cliente in clientes_na_pagina]

    return {
        "total_in_page": len(clientes_na_pagina),
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size) if total else 0,
        "items": clientes_out,
    }