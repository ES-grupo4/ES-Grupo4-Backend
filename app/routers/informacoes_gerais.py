from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session
from ..models.models import InformacoesGerais
from ..models.db_setup import get_bd
from ..schemas.informacoes_gerais import InformacoesGeraisIn

informacoes_gerais_router = APIRouter(
    prefix="/informacoes-gerais",
    tags=["Informações Gerais"],
)

router = informacoes_gerais_router


@router.get(
    "/",
    summary="Pega as informações gerais",
    tags=["Informações Gerais"],
    response_model=InformacoesGerais,
)
def read_info(db: Session = Depends(get_bd)):
    info = get_informacoes_gerais(db)
    if not info:
        raise HTTPException(
            status_code=404, detail="Informações gerais não encontradas."
        )
    return info


@router.put(
    "/",
    summary="Atualiza as informações gerais",
    tags=["Informações Gerais"],
    response_model=InformacoesGerais,
)
def update_info(data: InformacoesGeraisIn, db: Session = Depends(get_bd)):
    try:
        record = db.query(InformacoesGerais).first()
        if not record:
            record = InformacoesGerais()
            db.add(record)
        else:
            for field, value in data.model_dump().items():
                setattr(record, field, value)
        db.commit()
        db.refresh(record)
        return record
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def get_informacoes_gerais(db: Session) -> InformacoesGerais | None:
    return db.query(InformacoesGerais).first()


def update_informacoes_gerais(
    db: Session, data: InformacoesGeraisIn
) -> InformacoesGerais:
    record = db.query(InformacoesGerais).first()
    if not record:
        record = InformacoesGerais()
        db.add(record)
    else:
        for field, value in data.model_dump().items():
            setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record
