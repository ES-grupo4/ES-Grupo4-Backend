from typing import Annotated
from pydantic import BaseModel, StringConstraints
from typing import Annotated, Optional
from pydantic import BaseModel, StringConstraints


class ClienteIn(BaseModel):
    cpf: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=11)]
    nome: str
    matricula: str
    tipo: str
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
    nome: Optional[str] = None
    matricula: Optional[str] = None
    graduando: Optional[bool] = None
    pos_graduando: Optional[bool] = None
    bolsista: Optional[bool] = None