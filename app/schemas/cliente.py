from pydantic import BaseModel, ConfigDict


class ClienteIn(BaseModel):
    cpf: str
    nome: str
    senha: str
    email: str
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

    model_config = ConfigDict(from_attributes=True)