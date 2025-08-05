import os
from typing import Annotated
from fastapi import Depends

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .models import Base

bd_url = os.environ.get("DATABASE_URL")
engine = create_engine(  # Na CI a url do BD é diferente e é settada nessa ENV
    bd_url if bd_url else "postgresql+psycopg://nois:senha_massa@localhost:5432/ru_bd"
)


def get_bd():
    """
    Cria uma conexão com o BD,
     commita as mudanças se nenhum erro ocorrer e fecha a conexão depois.
    """
    with Session(engine) as bd:
        yield bd


Base.metadata.create_all(engine)

conexao_bd = Annotated[Session, Depends(get_bd)]
