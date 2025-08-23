from datetime import date
from sqlalchemy.orm import Session
from ..models.models import HistoricoAcoes


def guarda_acao(
    db: Session, id_ator: int, id_alvo: int | None, info_adicional: dict | None = None
) -> None:
    db.add(
        HistoricoAcoes(
            usuario_id_ator=id_ator,
            usuario_id_alvo=id_alvo,
            informacoes_acao=info_adicional,  # Mudar esse nome mds
            data=date.today(),
        )
    )
