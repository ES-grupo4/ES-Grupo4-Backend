from enum import Enum
from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints
from datetime import date
from typing import Annotated


class tipoFuncionarioEnum(str, Enum):
    funcionario = "funcionario"
    admin = "admin"


class FuncionarioOut(BaseModel):
    id: int
    nome: str
    cpf: str
    email: EmailStr | None
    tipo: tipoFuncionarioEnum
    data_entrada: date
    data_saida: date | None


class FuncionarioIn(BaseModel):
    cpf: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=11, max_length=14)
    ]
    nome: str
    senha: str
    email: EmailStr
    tipo: tipoFuncionarioEnum
    data_entrada: date

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cpf": "19896507406",
                "nome": "John Doe",
                "senha": "John123!",
                "email": "john@doe.com",
                "tipo": "admin",
                "data_entrada": "2024-05-08",
            }
        }
    )


class FuncionarioEdit(BaseModel):
    nome: str | None = None
    senha: str | None = None
    email: EmailStr | None = None
    tipo: tipoFuncionarioEnum | None = None
    data_entrada: date | None = None
    data_saida: date | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "John Dois",
                "senha": "John123!",
                "email": "john@doe.com",
                "tipo": "admin",
                "data_entrada": "2025-08-07",
                "data_saida": None
            }
        }
    )
