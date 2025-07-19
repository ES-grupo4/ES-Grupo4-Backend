from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.repository.database import SessionLocal
import io
import polars as pl
from sqlalchemy.orm import Session
from ..models.models import Funcionario
from ..models.db_setup import conexao_bd
from ..schemas.funcionario import FuncionarioOut

from sqlalchemy import select

funcionarios_router = APIRouter(
    prefix="/funcionario",
    tags=["Funcionário"],
)
router = funcionarios_router


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload-csv/", summary="Faz upload de funcionários via CSV")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):  # type: ignore
        raise HTTPException(status_code=400, detail="O arquivo deveria ser CSV.")

    contents = await file.read()
    try:
        table_from_csv = pl.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro lendo CSV: {e}")

    required_columns = {"usuario_id", "tipo", "senha", "email"}
    if not required_columns.issubset(set(table_from_csv.columns)):
        raise HTTPException(
            status_code=400, detail="O CSV não contém as colunas necessárias."
        )

    inserted = 0
    for row in table_from_csv.iter_rows(named=True):
        try:
            funcionario = Funcionario(
                usuario_id=int(row["usuario_id"]),
                tipo=str(row["cpf"]),
                senha=str(row["senha"]),
                email=str(row["email"]),
            )
            db.add(funcionario)
            db.commit()
            inserted += 1
        except Exception as e:
            print(f"Error inserting {row['name']}: {e}")
            db.rollback()
            continue

    return {"message": f"{inserted} employees successfully inserted."}


# Sempre preencham summary e tags
# Tags fazem sentido de ir nos APIRouter tmb
@router.post(
    "/{cpf}/{nome}",
    summary="Cria um funcionário",
)
def funcionario(cpf: str, nome: str, db: conexao_bd):
    """
    Imaginem que eu fiz um 'FuncionarioIn'
    """
    usuario = Funcionario(cpf=cpf, nome=nome, senha="a", email="a", tipo="admin")
    db.add(usuario)
    return {"message": "Funcionário criado com sucesso"}


@router.get(
    "/",
    summary="Pega todos os funcionários",
    tags=["Funcionário"],
    response_model=list[FuncionarioOut],
)
def funcionarios(db: conexao_bd):
    usuarios = db.scalars(select(Funcionario)).all()
    return usuarios
