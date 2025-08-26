from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.seguranca import gerar_hash
from ..models.models import HistoricoAcoes, Usuario

from enum import Enum


class AcoesEnum(str, Enum):
    CADASTRAR_FUNCIONARIO = "cadastrou funcionário"
    ATUALIZAR_FUNCIONARIO = "atualizou funcionário"
    DELETAR_FUNCIONARIO = "deletou funcionário"
    ATUALIZAR_INFOS_GERAIS = "atualizou informações gerais"
    CADASTRAR_COMPRA = "cadastrou compra"
    CADASTRAR_CLIENTE = "cadastrou cliente"
    ATUALIZAR_CLIENTE = "atualizou cliente"
    DELETAR_CLIENTE = "deletou cliente"


def guarda_acao(
    db: Session,
    acao: AcoesEnum,
    cpf_ator: str,
    id_alvo: int | None = None,
    info_adicional: dict | None = None,
) -> None:
    query = select(Usuario).where(Usuario.cpf_hash == gerar_hash(cpf_ator))
    ator = db.scalars(query).first()

    try:
        db.add(
            HistoricoAcoes(
                usuario_id_ator=ator.id,
                usuario_id_alvo=id_alvo,
                acao=acao,
                info=info_adicional,
                data=datetime.now(),
            )
        )
    except Exception as e:
        raise HTTPException(400, f"Erro guardando ação: {e}")
