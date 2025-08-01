from fastapi import APIRouter, UploadFile, File, HTTPException, Query
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


@compra_router.post(
    "/cadastra-compra",
    summary="Cadastra uma compra no sistema",
)
def cadastra_compra(compra: CompraIn, db: conexao_bd):
    nova_compra = Compra(
        usuario_id=compra.usuario_id,
        horario=compra.horario,
        local=compra.local,
        forma_pagamento=compra.forma_pagamento,
    )
    db.add(nova_compra)
    return {"message": "Compra cadastrada com sucesso"}


@compra_router.post(
    "/cadastra-compra-csv", summary="Cadastra uma compra no sistema por meio de csv"
)
async def cadastra_compra_csv(db: conexao_bd, file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):  # type: ignore
        raise HTTPException(status_code=400, detail="O arquivo deveria ser CSV.")

    contents = await file.read()
    try:
        table_from_csv = pl.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro lendo CSV: {e}")

    required_columns = {
        "usuario_id",
        "horario",
        "local",
        "forma_pagamento",
        "tipo_cliente",
    }
    if not required_columns.issubset(set(table_from_csv.columns)):
        raise HTTPException(
            status_code=400, detail="O CSV não contém as colunas necessárias."
        )

    inserted = 0
    for row in table_from_csv.iter_rows(named=True):
        try:
            compra = Compra(
                usuario_id=int(row["usuario_id"]),
                horario=datetime.strptime(row["horario"], "%Y-%m-%d %H:%M:%S"),
                local=str(row["local"]),
                forma_pagamento=str(row["forma_pagamento"]),
                tipo_cliente=str(row["tipo_cliente"]),
            )
            db.add(compra)
            db.commit()
            inserted += 1
        except Exception as e:
            print(f"Error inserting {row['name']}: {e}")
            db.rollback()
            continue

    return {"message": f"{inserted} employees successfully inserted."}


@compra_router.get(
    "/retorna-compras",
    summary="Retorna todas as compras cadastradas",
    tags=["Compra"],
    response_model=list[CompraOut],
)
def compras(db: conexao_bd):
    compras = db.scalars(select(Compra)).all()
    return compras


@compra_router.get(
    "/filtra-compras",
    summary="Retorna compras a partir de um filtro",
    tags=["Compra"],
    response_model=list[CompraOut],
)
def filtra_compra(
    db: conexao_bd, coluna: str = Query(...), parametro: str = Query(...)
):
    coluna_valida = None

    if hasattr(Compra, coluna):
        coluna_valida = getattr(Compra, coluna)
    elif hasattr(Cliente, coluna):
        coluna_valida = getattr(Cliente, coluna)
    else:
        raise HTTPException(status_code=400, detail=f"Coluna '{coluna}' não encontrada")

    saida = (
        db.query(Compra)
        .join(Cliente, Compra.usuario_id == Cliente.usuario_id)
        .filter(coluna_valida == parametro)
        .all()
    )

    if not saida:
        raise HTTPException(status_code=404, detail="Nenhuma compra encontrada")

    return saida
