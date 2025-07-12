from sqlalchemy import Column, String
from app.repository.database import Base


class Funcionario(Base):
    __tablename__ = "funcionario"

    nome = Column(String, nullable=False)
    cpf = Column(String, primary_key=True, index=True)
