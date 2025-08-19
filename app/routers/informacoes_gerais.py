from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session
from ..core.permissoes import requer_permissao
from ..models.models import InformacoesGerais
from ..models.db_setup import get_bd
from ..schemas.informacoes_gerais import InformacoesGeraisDTO

informacoes_gerais_router = APIRouter(
    prefix="/informacoes-gerais",
    tags=["Informações Gerais"],
)

router = informacoes_gerais_router


@router.post(
    "/",
    summary="Cria ou substitui as informações gerais",
    response_model=InformacoesGeraisDTO,
    dependencies=[requer_permissao("admin")],
)
def create_or_replace_info(
    data: InformacoesGeraisDTO,
    db: Session = Depends(get_bd),
):
    # Remove registro existente se houver
    existente = db.query(InformacoesGerais).first()
    if existente:
        db.delete(existente)
        db.commit()

    # Cria novo registro com dados da requisição
    novo_registro = InformacoesGerais(**data.model_dump())
    db.add(novo_registro)
    db.commit()
    db.refresh(novo_registro)

    return novo_registro


@router.get(
    "/",
    summary="Pega as informações gerais",
    tags=["Informações Gerais"],
    response_model=InformacoesGeraisDTO,
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
    response_model=InformacoesGeraisDTO,
    dependencies=[requer_permissao("admin")],
)
def update_info(data: InformacoesGeraisDTO, db: Session = Depends(get_bd)):
    # tabela com apenas um registro
    try:
        record = db.query(InformacoesGerais).first()
        if not record:
            raise HTTPException(
                status_code=404, detail="Informações gerais não encontradas."
            )
        else:
            for field, value in data.model_dump().items():
                setattr(record, field, value)
        db.commit()
        db.refresh(record)
        return record
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


def get_informacoes_gerais(db: Session) -> InformacoesGerais | None:
    return db.query(InformacoesGerais).first()


def update_informacoes_gerais(
    db: Session, data: InformacoesGeraisDTO
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
