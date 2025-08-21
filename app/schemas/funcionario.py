from enum import Enum
from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints, Field
from datetime import date
from typing import Annotated
from ..core.seguranca import fernet


class tipoFuncionarioEnum(str, Enum):
    funcionario = "funcionario"
    admin = "admin"


class FuncionarioOut(BaseModel):
    id: int
    nome: str
    cpf: str = Field(..., description="CPF descriptografado")
    email: EmailStr | None
    tipo: tipoFuncionarioEnum
    data_entrada: date
    data_saida: date | None

    @classmethod
    def from_orm(cls, obj):
        data = obj.__dict__.copy()
        data["cpf"] = obj.get_cpf(fernet)
        return cls(**data)


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
                "cpf": "79920205451",
                "nome": "John Dois",
                "senha": "John123!",
                "email": "john@dois.com",
                "tipo": "funcionario",
                "data_entrada": f"{date.today()}",
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
                "nome": "John Tres",
                "senha": "John123!",
                "email": "john@tres.com",
                "tipo": "admin",
                "data_entrada": "2025-08-07",
                "data_saida": None,
            }
        }
    )


class FuncionarioPaginationOut(BaseModel):
    total_in_page: int
    page: int
    page_size: int
    total_pages: int
    items: list[FuncionarioOut]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_in_page": 2,
                "page": 1,
                "page_size": 10,
                "total_pages": 1,
                "items": [
                    {
                        "id": 1,
                        "nome": "John Doe",
                        "cpf": "79920205451",
                        "email": "john@doe.com",
                        "tipo": "funcionario",
                        "data_entrada": "2025-08-07",
                        "data_saida": None,
                    },
                    {
                        "id": 2,
                        "nome": "Jane Smith",
                        "cpf": "23456789012",
                        "email": "jane@smith.com",
                        "tipo": "admin",
                        "data_entrada": "2025-08-10",
                        "data_saida": None,
                    },
                ],
            }
        }
    )
