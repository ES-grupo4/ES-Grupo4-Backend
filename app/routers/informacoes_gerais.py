from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session
from ..models.models import InformacoesGerais
from ..schemas.informacoes_gerais import InformacoesGeraisUpdate
from ..schemas.informacoes_gerais import InformacoesGeraisResponse
from ..models.db_setup import get_bd

informacoes_gerais_router = APIRouter(
    prefix="/informacoes-gerais",
    tags=["Informações Gerais"],
)

router = informacoes_gerais_router


@router.get(
    "/",
    summary="Pega as informações gerais",
    tags=["Informações Gerais"],
    response_model=InformacoesGeraisResponse,
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
    response_model=InformacoesGeraisResponse,
)
def update_info(data: InformacoesGeraisUpdate, db: Session = Depends(get_bd)):
    try:
        return update_informacoes_gerais(db, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def get_informacoes_gerais(db: Session) -> InformacoesGerais | None:
    return db.query(InformacoesGerais).first()


def update_informacoes_gerais(
    db: Session, data: InformacoesGeraisUpdate
) -> InformacoesGerais:
    record = db.query(InformacoesGerais).first()
    if not record:
        record = InformacoesGerais(**data.model_dump())
        db.add(record)
    else:
        for field, value in data.model_dump().items():
            setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record
