from typing import Annotated
from fastapi import APIRouter, Depends, Path, HTTPException

from sqlalchemy import extract, select
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.historico_acoes import AcoesEnum, guarda_acao
from core.permissoes import requer_permissao

from models.models import Compra, Cliente, Funcionario
from ..models.db_setup import get_bd

from schemas.relatorio import RelatorioOut

relatorio_router = APIRouter(prefix="relatorio", tags=["Relatório"])
router = relatorio_router


@router.get(
    "/{ano}/{mes}",
    summary="Pega as informações necessárias para gerar um relatório mensal",
)
def relatorio_get(
    ator: Annotated[dict, Depends(requer_permissao("admin", "funcionario"))],
    bd: Session = Depends(get_bd),
    ano: int = Path(..., ge=1900, le=2100),
    mes: int = Path(..., ge=1, le=12),
) -> RelatorioOut:
    try:
        data = datetime.strptime(f"{ano}-{mes}", "%Y-%m")
    except ValueError as e:
        raise HTTPException(400, "Data inválida")

    query_compras = select(Compra).where(
        # 2. Add a condition to check the year of the 'horario' column
        extract("year", Compra.horario) == ano,
        # 3. Add a condition to check the month of the 'horario' column
        extract("month", Compra.horario) == mes,
    )
    query_funcionario = select(Funcionario).where(
        # 2. Add a condition to check the year of the 'horario' column
        extract("year", Funcionario.data_entrada) == ano,
        # 3. Add a condition to check the month of the 'horario' column
        extract("month", Funcionario.data_entrada) == mes,
    )

    return RelatorioOut()
