from enum import Enum
from typing import Annotated
from pydantic import BaseModel, StringConstraints, ConfigDict


class ClienteEnum(str, Enum):
    externo = "externo"
    professor = "professor"
    tecnico = "tecnico"
    aluno = "aluno"



class ClienteIn(BaseModel):
    cpf: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=11, max_length=14)
    ]
    nome: str
    matricula: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=9)
    ]
    tipo: ClienteEnum
    graduando: bool
    pos_graduando: bool
    bolsista: bool

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cpf": "394.108.619-77",
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
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "nome": "João Pedro",
                "cpf": "394.108.619-77",
                "subtipo": "regular",
                "matricula": "20240001",
                "tipo": "aluno",
                "graduando": True,
                "pos_graduando": False,
                "bolsista": True,
            }
        }
    )

class ClientePaginationOut(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
    items: list[ClienteOut]


class ClienteEdit(BaseModel):
    nome: str | None = None
    matricula: Annotated[
        str | None, StringConstraints(strip_whitespace=True, min_length=9, max_length=9)
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
