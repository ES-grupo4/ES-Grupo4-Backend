from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import polars as pl
from app.models.employee import Funcionario
from app.repository.database import SessionLocal
import io

router = APIRouter(prefix="/funcionario", tags=["Funcionários"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload-csv/", summary="Faz upload de funcionários via CSV")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="The file must be a CSV.")

    contents = await file.read()
    try:
        table_from_csv = pl.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {e}")

    required_columns = {"name", "cpf"}
    if not required_columns.issubset(set(table_from_csv.columns)):
        raise HTTPException(
            status_code=400, detail="CSV must contain 'name' and 'cpf' columns."
        )

    inserted = 0
    for row in table_from_csv.iter_rows(named=True):
        try:
            funcionario = Funcionario(nome=str(row["name"]), cpf=str(row["cpf"]))
            db.add(funcionario)
            db.commit()
            inserted += 1
        except Exception as e:
            print(f"Error inserting {row['name']}: {e}")
            db.rollback()
            continue

    return {"message": f"{inserted} employees successfully inserted."}
