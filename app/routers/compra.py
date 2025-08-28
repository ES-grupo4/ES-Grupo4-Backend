from typing import Annotated
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, status
import io
from math import ceil
import polars as pl
from sqlalchemy import select, func, or_
from app.core.historico_acoes import AcoesEnum, guarda_acao
from ..models.db_setup import conexao_bd
from ..models.models import Compra
from ..models.models import Cliente
from ..schemas.compra import CompraIn, CompraOut, CompraPaginationOut
from ..core.permissoes import requer_permissao
from datetime import datetime

compra_router = APIRouter(
    prefix="/compra",
    tags=["Compra"],
)
router = compra_router


@router.post(
    "/",
    summary="Cadastra uma compra no sistema",
    status_code=status.HTTP_201_CREATED,
)
def cadastra_compra(
    compra: CompraIn,
    ator: Annotated[dict, Depends(requer_permissao("funcionario", "admin"))],
    db: conexao_bd,
):
    nova_compra = Compra(
        usuario_id=compra.usuario_id,
        horario=compra.horario,
        local=compra.local,
        forma_pagamento=compra.forma_pagamento,
    )
    db.add(nova_compra)
    db.flush()
    guarda_acao(
        db,
        AcoesEnum.CADASTRAR_COMPRA,
        ator["cpf"],
        info_adicional=CompraOut.model_validate(nova_compra).model_dump_json(),
    )
    return {"message": "Compra cadastrada com sucesso"}


@router.post(
    "/csv",
    summary="Cadastra uma compra no sistema por meio de csv",
)
async def cadastra_compra_csv(
    db: conexao_bd,
    ator: Annotated[dict, Depends(requer_permissao("funcionario", "admin"))],
    arquivo: UploadFile = File(...),
):
    if not arquivo.filename.endswith(".csv"):  # type: ignore
        raise HTTPException(status_code=400, detail="O arquivo deveria ser CSV.")

    contents = await arquivo.read()
    try:
        tabela_csv = pl.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro lendo CSV: {e}")

    required_columns = {
        "usuario_id",
        "horario",
        "local",
        "forma_pagamento",
    }
    if not required_columns.issubset(set(tabela_csv.columns)):
        raise HTTPException(
            status_code=422, detail="O CSV não contém as colunas necessárias."
        )

    inseridas = 0
    compras = []
    for linha in tabela_csv.iter_rows(named=True):
        try:
            compra = Compra(
                usuario_id=int(linha["usuario_id"]),
                horario=datetime.fromisoformat(linha["horario"]),
                local=str(linha["local"]),
                forma_pagamento=str(linha["forma_pagamento"]),
            )
            db.add(compra)
            db.flush()
            compras.append(compra)
            inseridas += 1
        except Exception as e:
            raise HTTPException(
                status_code=422, detail=f"Erro ao cadastrar {linha}: {e}"
            )

    for compra in compras:
        guarda_acao(
            db,
            AcoesEnum.CADASTRAR_COMPRA,
            ator["cpf"],
            None,
            info_adicional=CompraOut.model_validate(compra).model_dump_json(),
        )

    return {"message": f"{inseridas} compra(s) cadastrada(s) com sucesso."}


@router.get(
    "/",
    summary="Retorna compras (com filtros opcionais)",
    tags=["Compra"],
    response_model=CompraPaginationOut,
    dependencies=[Depends(requer_permissao("funcionario", "admin"))],
)
def filtra_compra(
    db: conexao_bd,
    horario: datetime | None = Query(
        default=None, description="Filtra por horário da compra"
    ),
    local: str | None = Query(default=None, description="Filtra por local da compra"),
    forma_pagamento: str | None = Query(
        default=None, description="Filtra por forma de pagamento da compra"
    ),
    comprador: str | None = Query(
        default=None, description="Filtra por comprador responsável pela compra"
    ),
    categoria_comprador: str | None = Query(
        default=None, description="Filtra por categoria do comprador"
    ),
    page: int = Query(1, ge=1, description="Número da página (padrão 1)"),
    page_size: int = Query(
        10, ge=1, le=100, description="Quantidade de compras por página (padrão 10)"
    ),
):
    query = select(Compra).join(Cliente, Compra.usuario_id == Cliente.usuario_id)

    if horario is not None:
        query = query.where(Compra.horario == horario)
    if local is not None:
        query = query.where(Compra.local.ilike(f"%{local}%"))
    if forma_pagamento is not None:
        query = query.where(Compra.forma_pagamento.ilike(f"%{forma_pagamento}%"))
    if comprador is not None:
        query = query.where(Cliente.nome.ilike(f"%{comprador}%"))
    if categoria_comprador is not None:
        query = query.where(Cliente.tipo.ilike(f"%{categoria_comprador}%"))

    offset = (page - 1) * page_size
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    compras_na_pagina = db.scalars(query.offset(offset).limit(page_size)).all()
    compras_out = [
        CompraOut.model_validate(c, from_attributes=True) for c in compras_na_pagina
    ]

    return {
        "total_in_page": len(compras_na_pagina),
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size) if total else 0,
        "items": compras_out,
    }


@router.get(
    "/lista",
    summary="Lista compras a partir de uma string aplicada a multiplas colunas",
    tags=["Compra"],
    response_model=CompraPaginationOut,
    dependencies=[Depends(requer_permissao("funcionario", "admin"))],
)
def listar_compras(
    db: conexao_bd,
    busca: str | None = Query(
        default=None,
        description=(
            "String aplicada a data, local, forma de pagamento, comprador e categoria comprador"
        ),
    ),
    page: int = Query(1, ge=1, description="Número da página (padrão 1)"),
    page_size: int = Query(
        10, ge=1, le=100, description="Quantidade de compras por página (padrão 10)"
    ),
):
    query = select(Compra).join(Cliente, Compra.usuario_id == Cliente.usuario_id)

    if busca:
        busca_like = f"%{busca}%"
        filtro = []

        filtro.append(Compra.local.ilike(busca_like))
        filtro.append(Compra.forma_pagamento.ilike(busca_like))
        filtro.append(Cliente.nome.ilike(busca_like))
        filtro.append(Cliente.tipo.ilike(busca_like))

        parsed_datetime = None
        try:
            parsed_datetime = datetime.fromisoformat(busca)
        except ValueError:
            pass
        filtro.append(Compra.horario == parsed_datetime)

        query = query.where(or_(*filtro))

    offset = (page - 1) * page_size
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    compras_na_pagina = db.scalars(query.offset(offset).limit(page_size)).all()
    compras_out = [
        CompraOut.model_validate(c, from_attributes=True) for c in compras_na_pagina
    ]

    return {
        "total_in_page": len(compras_na_pagina),
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size) if total else 0,
        "items": compras_out,
    }
