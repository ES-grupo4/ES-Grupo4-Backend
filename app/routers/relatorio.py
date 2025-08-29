from typing import Annotated
from fastapi import APIRouter, Depends, Path, HTTPException

from sqlalchemy import extract, select, func
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.historico_acoes import AcoesEnum, guarda_acao
from core.permissoes import requer_permissao

from models.models import Compra, Cliente, Funcionario
from routers.informacoes_gerais import read_info
from ..models.db_setup import get_bd

from schemas.relatorio import PorTipoCliente, RelatorioOut

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
    nome_empresa = read_info(bd).nome_empresa

    query_compras_mes = select(Compra).where(
        extract("year", Compra.horario) == ano,
        extract("month", Compra.horario) == mes,
    )
    faturamento_mensal = bd.scalar(
        select(func.sum(Compra.preco_compra)).select_from(query_compras_mes.subquery())
    )

    query_funcionarios_novos = select(Funcionario).where(
        extract("year", Funcionario.data_entrada) == ano,
        extract("month", Funcionario.data_entrada) == mes,
    )
    num_adicionados = bd.scalar(
        select(func.count()).select_from(query_funcionarios_novos.subquery())
    )
    num_funcionarios = bd.scalar(
        select(func.count()).select_from(
            select(Funcionario).where(Funcionario.tipo == "funcionario").subquery()
        )
    )
    num_admins = bd.scalar(
        select(func.count()).select_from(
            select(Funcionario).where(Funcionario.tipo == "admin").subquery()
        )
    )
    num_desativados = bd.scalar(
        select(func.count()).select_from(
            select(Funcionario).where(Funcionario.data_saida.is_not(None)).subquery()
        )
    )

    return RelatorioOut(
        nome_empresa=nome_empresa,
        faturamento_bruto_mensal=faturamento_mensal or 0,
        clientes_registrados=PorTipoCliente(),
        funcionarios_ativos=num_funcionarios or 0,
        administradores_ativos=num_admins or 0,
        desativados=num_desativados or 0,
        funcionarios_adicionados_mes=num_adicionados or 0,
        compras_por_tipo=PorTipoCliente(),
    )
