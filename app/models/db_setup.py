from typing import Annotated
from fastapi import Depends

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .models import Base

engine = create_engine("sqlite:///odio.db", connect_args={"check_same_thread": False})


def get_bd():
    """
    Cria uma conexão com o BD,
     commita as mudanças se nenhum erro ocorrer e fecha a conexão depois.
    """
    bd = Session(engine)
    try:
        yield bd
        bd.commit()
    except:
        bd.rollback()
        raise
    finally:
        bd.close()


Base.metadata.create_all(engine)

conexao_bd = Annotated[Session, Depends(get_bd)]
