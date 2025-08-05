from enum import Enum
from typing import Annotated
from pydantic import BaseModel, StringConstraints, field_validator, ConfigDict


class ClienteEnum(str, Enum):
    externo = "externo"
    professor = "professor"
    tecnico = "tecnico"
    aluno = "aluno"


class ClienteIn(BaseModel):
    cpf: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=11, max_length=11)
    ]
    nome: str
    matricula: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=9)
    ]
    tipo: ClienteEnum
    graduando: bool
    pos_graduando: bool
    bolsista: bool

    @field_validator("cpf")
    @classmethod
    def cpf_deve_conter_apenas_digitos(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("O CPF deve conter somente dígitos numéricos.")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cpf": "12345678901",
                "nome": "João Pedro",
                "matricula": "20240001",
                "tipo": "aluno",
                "graduando": True,
                "pos_graduando": False,
                "bolsista": True,
            }
        }
    )


class ClienteOut(BaseModel):
    id: int
    nome: str
    cpf: str
    subtipo: str
    matricula: str
    tipo: ClienteEnum
    graduando: bool
    pos_graduando: bool
    bolsista: bool

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "nome": "João Pedro",
                "cpf": "12345678901",
                "subtipo": "regular",
                "matricula": "20240001",
                "tipo": "aluno",
                "graduando": True,
                "pos_graduando": False,
                "bolsista": True,
            }
        }
    )


class ClienteEdit(BaseModel):
    nome: str | None = None
    matricula: Annotated[
        str | None, StringConstraints(strip_whitespace=True, max_length=9)
    ] = None
    tipo: ClienteEnum | None = None
    graduando: bool | None = None
    pos_graduando: bool | None = None
    bolsista: bool | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "João Pedro Editado",
                "matricula": "20240002",
                "tipo": "professor",
                "graduando": False,
                "pos_graduando": True,
                "bolsista": False,
            }
        }
    )
