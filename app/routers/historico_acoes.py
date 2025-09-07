import json
from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, extract
from sqlalchemy.orm import aliased

from app.core.seguranca import descriptografa_cpf
from app.schemas.acoes import AcaoPaginationOut

from ..core.permissoes import requer_permissao
from ..models.db_setup import conexao_bd
from ..models.models import HistoricoAcoes, Usuario

acoes_router = APIRouter(
    prefix="/app/historico_acoes",
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
    ator = aliased(Usuario, name="ator")
    alvo = aliased(Usuario, name="alvo")

    query = (
        select(HistoricoAcoes, ator, alvo)
        .join(ator, HistoricoAcoes.usuario_id_ator == ator.id)
        .join(alvo, HistoricoAcoes.usuario_id_alvo == alvo.id, isouter=True)
    )

    # filtro por mês/ano
    if mes is not None and ano is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se 'mes' for informado, 'ano' também deve ser fornecido",
        )

    if mes is not None and ano is not None:
        query = query.where(
            extract("month", HistoricoAcoes.data) == mes,
            extract("year", HistoricoAcoes.data) == ano,
        )

    elif ano is not None:
        query = query.where(
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
