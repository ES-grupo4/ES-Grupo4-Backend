from enum import Enum
from pydantic import BaseModel, ConfigDict, EmailStr


class tipoFuncionarioEnum(str, Enum):
    funcionario = "funcionario"
    admin = "admin"

class FuncionarioOut(BaseModel):
    id: int
    nome: str
    cpf: str
    email: EmailStr
    tipo: tipoFuncionarioEnum


class FuncionarioIn(BaseModel):
    cpf: str
    nome: str
    senha: str
    email: EmailStr
    tipo: tipoFuncionarioEnum

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cpf": "198.965.074-06",
                "nome": "John Doe",
                "senha": "John123!",
                "email": "john@doe.com",
                "tipo": "admin",
            }
        }
    )

class FuncionarioEdit(BaseModel):
    nome: str
    senha: str
    email: EmailStr
    tipo: tipoFuncionarioEnum

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "John Dois",
                "senha": "John123!",
                "email": "john@doe.com",
                "tipo": "admin",
            }
        }
    )