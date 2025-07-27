from enum import Enum
from typing import Annotated

from pydantic import BaseModel, constr


class TipoClienteEnum(str, Enum):
    externo = "externo"
    professor = "professor"
    tecnico = "tecnico"
    aluno = "aluno"

# Validação de CPF: exatamente 11 dígitos numéricos
CPFStr = constr(strip_whitespace=True, min_length=11, max_length=11, regex=r'^\d{11}$')
# Validação de matrícula: de 1 até 9 caracteres, sem espaços extras
MatriculaStr = constr(strip_whitespace=True, min_length=1, max_length=9)


class ClienteIn(BaseModel):
    cpf: CPFStr
    nome: str
    matricula: MatriculaStr
    tipo: TipoClienteEnum
    graduando: bool
    pos_graduando: bool
    bolsista: bool


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
        str | None,
        constr(strip_whitespace=True, max_length=9)
    ] = None
    tipo: TipoClienteEnum | None = None
    graduando: bool | None = None
    pos_graduando: bool | None = None
    bolsista: bool | None = None
