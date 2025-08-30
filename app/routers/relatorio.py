from typing import Annotated
from fastapi import APIRouter, Depends, Path

from sqlalchemy import Subquery, extract, select, func
from sqlalchemy.orm import Session
from core.permissoes import requer_permissao

from models.models import Compra, Cliente, Funcionario
from routers.informacoes_gerais import read_info
from ..models.db_setup import get_bd

from schemas.relatorio import AlunosRegistrados, PorTipoCliente, RelatorioOut

relatorio_router = APIRouter(prefix="relatorio", tags=["Relatório"])
router = relatorio_router


def retorna_clientes_registrados(bd: Session, query_alunos_totais: Subquery):
    num_externos = bd.scalar(
        select(func.count()).select_from(
            select(Cliente).where(Cliente.tipo == "externo").subquery()
        )
    )
    num_professores = bd.scalar(
        select(func.count()).select_from(
            select(Cliente).where(Cliente.tipo == "professor").subquery()
        )
    )
    num_tecnicos = bd.scalar(
        select(func.count()).select_from(
            select(Cliente).where(Cliente.tipo == "tecnico").subquery()
        )
    )

    num_clientes_totais = bd.scalar(select(func.count()).select_from(Cliente))

    num_alunos_totais = bd.scalar(select(func.count()).select_from(query_alunos_totais))
    num_pos_graduacao = bd.scalar(
        select(func.count())
        .select_from(query_alunos_totais)
        .where(
            query_alunos_totais.columns.graduando.is_(False),
            query_alunos_totais.columns.pos_graduando.is_(True),
        )
    )
    num_graduacao = bd.scalar(
        select(func.count())
        .select_from(query_alunos_totais)
        .where(
            query_alunos_totais.columns.graduando.is_(True),
            query_alunos_totais.columns.pos_graduando.is_(False),
        )
    )
    num_graduacao_e_pos_graduacao = bd.scalar(
        select(func.count())
        .select_from(query_alunos_totais)
        .where(
            query_alunos_totais.columns.graduando.is_(True),
            query_alunos_totais.columns.pos_graduando.is_(True),
        )
    )
    num_bolsistas = bd.scalar(
        select(func.count())
        .select_from(query_alunos_totais)
        .where(
            query_alunos_totais.columns.bolsista.is_(True),
        )
    )

    return PorTipoCliente(
        total=num_clientes_totais or 0,
        externos=num_externos or 0,
        professores=num_professores or 0,
        tecnicos=num_tecnicos or 0,
        alunos=AlunosRegistrados(
            total=num_alunos_totais or 0,
            pos_graduacao=num_pos_graduacao or 0,
            em_graduacao=num_graduacao or 0,
            ambos=num_graduacao_e_pos_graduacao or 0,
            bolsistas=num_bolsistas or 0,
        ),
    )


def retorna_compras_por_tipo(
    bd: Session, query_compras_mes: Subquery, query_alunos_totais: Subquery
):
    clientes_totais = select(Cliente.id)
    compras_totais = bd.scalar(
        select(func.count())
        .select_from(query_compras_mes)
        .where(query_compras_mes.columns.usuario_id.in_(clientes_totais))
    )

    clientes_externos = clientes_totais.where(Cliente.tipo == "externo")
    clientes_professores = clientes_totais.where(Cliente.tipo == "professor")
    clientes_tecnicos = clientes_totais.where(Cliente.tipo == "tecnico")

    compras_externos = bd.scalar(
        select(func.count())
        .select_from(query_compras_mes)
        .where(
            query_compras_mes.columns.usuario_id.in_(clientes_externos),
        )
    )
    compras_professores = bd.scalar(
        select(func.count())
        .select_from(query_compras_mes)
        .where(
            query_compras_mes.columns.usuario_id.in_(clientes_professores),
        )
    )
    compras_tecnicos = bd.scalar(
        select(func.count())
        .select_from(query_compras_mes)
        .where(
            query_compras_mes.columns.usuario_id.in_(clientes_tecnicos),
        )
    )

    alunos_total = clientes_totais.where(Cliente.tipo == "aluno")
    compras_totais_alunos = bd.scalar(
        select(func.count())
        .select_from(query_compras_mes)
        .where(query_compras_mes.columns.usuario_id.in_(alunos_total))
    )
    compras_pos_graduacao = bd.scalar(
        select(func.count())
        .select_from(query_compras_mes)
        .where(
            query_compras_mes.columns.usuario_id.in_(
                select(query_alunos_totais.columns.id).where(
                    query_alunos_totais.columns.graduando.is_(False),
                    query_alunos_totais.columns.pos_graduando.is_(True),
                )
            )
        )
    )
    compras_graduacao = bd.scalar(
        select(func.count())
        .select_from(query_compras_mes)
        .where(
            query_compras_mes.columns.usuario_id.in_(
                select(query_alunos_totais.columns.id).where(
                    query_alunos_totais.columns.graduando.is_(True),
                    query_alunos_totais.columns.pos_graduando.is_(False),
                )
            )
        )
    )
    compras_graduacao_e_pos_graduacao = bd.scalar(
        select(func.count())
        .select_from(query_compras_mes)
        .where(
            query_compras_mes.columns.usuario_id.in_(
                select(query_alunos_totais.columns.id).where(
                    query_alunos_totais.columns.graduando.is_(True),
                    query_alunos_totais.columns.pos_graduando.is_(True),
                )
            )
        )
    )
    compras_bolsistas = bd.scalar(
        select(func.count())
        .select_from(query_compras_mes)
        .where(
            query_compras_mes.columns.usuario_id.in_(
                select(query_alunos_totais.columns.id).where(
                    query_alunos_totais.columns.bolsista.is_(True),
                )
            )
        )
    )

    return PorTipoCliente(
        total=compras_totais or 0,
        externos=compras_externos or 0,
        professores=compras_professores or 0,
        tecnicos=compras_tecnicos or 0,
        alunos=AlunosRegistrados(
            total=compras_totais_alunos or 0,
            pos_graduacao=compras_pos_graduacao or 0,
            em_graduacao=compras_graduacao or 0,
            ambos=compras_graduacao_e_pos_graduacao or 0,
            bolsistas=compras_bolsistas or 0,
        ),
    )


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

    query_alunos_totais = (
        select(Cliente.id, Cliente.graduando, Cliente.pos_graduando, Cliente.bolsista)
        .where(Cliente.tipo == "aluno")
        .subquery()
    )

    clientes_registrados = retorna_clientes_registrados(
        bd=bd, query_alunos_totais=query_alunos_totais
    )

    compras_por_tipo = retorna_compras_por_tipo(
        bd=bd,
        query_compras_mes=query_compras_mes.subquery(),
        query_alunos_totais=query_alunos_totais,
    )

    return RelatorioOut(
        nome_empresa=nome_empresa,
        faturamento_bruto_mensal=faturamento_mensal or 0,
        clientes_registrados=clientes_registrados,
        funcionarios_ativos=num_funcionarios or 0,
        administradores_ativos=num_admins or 0,
        desativados=num_desativados or 0,
        funcionarios_adicionados_mes=num_adicionados or 0,
        compras_por_tipo=compras_por_tipo,
    )
