from fastapi import APIRouter
from sqlalchemy import select

from ..core.permissoes import requer_permissao
from ..models.db_setup import conexao_bd
from ..models.models import HistoricoAcoes, Usuario

acoes_router = APIRouter(
    prefix="/historico_acoes",
    tags=["/historico_acoes"],
    dependencies=[requer_permissao("admin")],
)

router = acoes_router


@router.get("/", summary="Lista ações realizadas por usuários")
def pega_acoes(db: conexao_bd):
    query = select(HistoricoAcoes).join(
        Usuario, HistoricoAcoes.usuario_id_ator == Usuario.id
    )
    out = db.scalars(query).all()
    return out
