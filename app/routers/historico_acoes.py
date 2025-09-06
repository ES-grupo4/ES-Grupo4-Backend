from datetime import date
import json
from math import ceil
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, extract
from sqlalchemy.orm import aliased

from app.core.historico_acoes import AcoesEnum
from app.core.seguranca import descriptografa_cpf, gerar_hash
from app.schemas.acoes import AcaoPaginationOut

from ..core.permissoes import requer_permissao
from ..models.db_setup import conexao_bd
from ..models.models import HistoricoAcoes, Usuario

acoes_router = APIRouter(
    prefix="/historico_acoes",
    tags=["Histórico de Ações"],
)

router = acoes_router


@router.get(
    "/",
    summary="Lista ações realizadas por funcionários",
    response_model=AcaoPaginationOut,
    dependencies=[Depends(requer_permissao("admin"))],
)
def pega_acoes(
    db: conexao_bd,
    tipo_acao: AcoesEnum | None = Query(default=None),
    id_ator: int | None = Query(default=None),
    nome_ator: str | None = Query(default=None),
    cpf_ator: str | None = Query(default=None),
    id_alvo: int | None = Query(default=None),
    nome_alvo: str | None = Query(default=None),
    cpf_alvo: str | None = Query(default=None),
    data_inicio: date | None = Query(
        default=None, description="Filtrar ações a partir desta data"
    ),
    data_fim: date | None = Query(
        default=None, description="Filtrar ações até esta data"
    ),
    mes: int | None = Query(
        default=None, ge=1, le=12, description="Mês específico para filtrar"
    ),
    ano: int | None = Query(
        default=None,
        description="Ano específico para filtrar (obrigatório se mes for usado)",
    ),
    page: int = Query(1, ge=1, description="Número da página (padrão 1)"),
    page_size: int = Query(
        10, ge=1, le=100, description="Quantidade de registros por página (padrão 10)"
    ),
):
    Ator = aliased(Usuario, name="ator")
    Alvo = aliased(Usuario, name="alvo")

    query = (
        select(HistoricoAcoes, Ator, Alvo)
        .join(Ator, HistoricoAcoes.usuario_id_ator == Ator.id)
        .join(Alvo, HistoricoAcoes.usuario_id_alvo == Alvo.id, isouter=True)
    )

    # filtros de usuário e ação
    if id_ator is not None:
        query = query.where(Ator.id == id_ator)
    if nome_ator is not None:
        query = query.where(Ator.nome == nome_ator)
    if cpf_ator is not None:
        query = query.where(Ator.cpf == cpf_ator)
    if id_alvo is not None:
        query = query.where(Alvo.id == id_alvo)
    if nome_alvo is not None:
        query = query.where(Alvo.nome == nome_alvo)
    if cpf_alvo is not None:
        query = query.where(Alvo.cpf_hash == gerar_hash(cpf_alvo))
    if tipo_acao is not None:
        query = query.where(HistoricoAcoes.acao == tipo_acao)

    # filtros por data
    if data_inicio is not None:
        query = query.where(HistoricoAcoes.data >= data_inicio)
    if data_fim is not None:
        query = query.where(HistoricoAcoes.data <= data_fim)

    # filtro por mês/ano
    if mes is not None:
        if ano is None:
            raise HTTPException(
                400, "Se 'mes' for informado, 'ano' também deve ser fornecido"
            )
        query = query.where(
            extract("month", HistoricoAcoes.data) == mes,
            extract("year", HistoricoAcoes.data) == ano,
        )

    # paginação
    offset = (page - 1) * page_size
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    acoes_na_pagina = db.execute(query.offset(offset).limit(page_size)).all()

    itens = [
        {
            "id": historico.id,
            "ator_id": ator.id,
            "ator_nome": ator.nome,
            "ator_cpf": descriptografa_cpf(ator.cpf_cript),
            "acao": historico.acao,
            "alvo_id": alvo.id if alvo else None,
            "alvo_nome": alvo.nome if alvo else None,
            "alvo_cpf": descriptografa_cpf(alvo.cpf_cript) if alvo else None,
            "data": historico.data,
            "info_adicional": json.loads(historico.info) if historico.info else {},
        }
        for historico, ator, alvo in acoes_na_pagina
    ]

    return {
        "total_in_page": len(acoes_na_pagina),
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size) if total else 0,
        "items": itens,
    }
