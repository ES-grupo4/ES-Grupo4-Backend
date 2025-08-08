from fastapi import APIRouter, UploadFile, File, HTTPException, Query, status
import io
import polars as pl
from sqlalchemy import select
from ..models.db_setup import conexao_bd
from ..models.models import Compra
from ..models.models import Cliente
from ..schemas.compra import CompraIn, CompraOut
from datetime import datetime

compra_router = APIRouter(prefix="/compra", tags=["Compra"])
router = compra_router


@router.post(
    "/",
    summary="Cadastra uma compra no sistema",
    status_code=status.HTTP_201_CREATED,
)
def cadastra_compra(compra: CompraIn, db: conexao_bd):
    nova_compra = Compra(
        usuario_id=compra.usuario_id,
        horario=compra.horario,
        local=compra.local,
        forma_pagamento=compra.forma_pagamento,
    )
    db.add(nova_compra)
    db.commit()
    return {"message": "Compra cadastrada com sucesso"}


@router.post(
    "/csv",
    summary="Cadastra uma compra no sistema por meio de csv",
)
async def cadastra_compra_csv(db: conexao_bd, arquivo: UploadFile = File(...)):
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
    for linha in tabela_csv.iter_rows(named=True):
        try:
            compra = Compra(
                usuario_id=int(linha["usuario_id"]),
                horario=datetime.fromisoformat(linha["horario"]),
                local=str(linha["local"]),
                forma_pagamento=str(linha["forma_pagamento"]),
            )
            db.add(compra)
            db.commit()
            inseridas += 1
        except Exception as e:
            raise HTTPException(
                status_code=422, detail=f"Erro ao cadastrar {linha}: {e}"
            )

    return {"message": f"{inseridas} compra(s) cadastrada(s) com sucesso."}


@router.get(
    "/",
    summary="Retorna compras a partir de um filtro",
    tags=["Compra"],
    response_model=list[CompraOut],
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
):
    query = (
        select(Compra)
        .select_from(Compra)
        .join(Cliente, Compra.usuario_id == Cliente.usuario_id)
    )

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

    saida = db.scalars(query).all()

    if not saida:
        raise HTTPException(
            status_code=404,
            detail="Nenhuma compra encontrada com os filtros fornecidos",
        )

    return saida
