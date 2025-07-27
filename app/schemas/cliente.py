from enum import Enum
from typing import Annotated

from pydantic import BaseModel, StringConstraints, field_validator


class TipoClienteEnum(str, Enum):
    externo = "externo"
    professor = "professor"
    tecnico = "tecnico"
    aluno = "aluno"


class ClienteIn(BaseModel):
    cpf: int
    nome: str
    matricula: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=9)
    ]
    tipo: TipoClienteEnum
    graduando: bool
    pos_graduando: bool
    bolsista: bool

    @field_validator("cpf")
    @classmethod
    def cpf_deve_ter_11_digitos(cls, v: int) -> int:
        cpf_str = str(v)
        if len(cpf_str) != 11 or not cpf_str.isdigit():
            raise ValueError("O CPF deve conter exatamente 11 dígitos numéricos.")
        return v


class ClienteOut(BaseModel):
    id: int
    nome: str
    cpf: str
    subtipo: str
    matricula: str
    tipo: str
    graduando: bool
    pos_graduando: bool
    bolsista: bool


class ClienteEdit(BaseModel):
    nome: str | None = None
    matricula: Annotated[
        str | None, StringConstraints(strip_whitespace=True, max_length=9)
    ] = None
    tipo: TipoClienteEnum | None = None
    graduando: bool | None = None
    pos_graduando: bool | None = None
    bolsista: bool | None = None
