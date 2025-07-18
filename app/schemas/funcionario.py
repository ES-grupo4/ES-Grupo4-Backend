from pydantic import BaseModel


class FuncionarioOut(BaseModel):
    """
    DTO do funcionário sem sua senha
    """

    id: int
    nome: str
    cpf: str
    email: str
    subtipo: str
