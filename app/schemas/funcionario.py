from pydantic import BaseModel, ConfigDict


class FuncionarioOut(BaseModel):
    """
    DTO do funcionário sem sua senha
    """

    id: int
    nome: str
    cpf: str
    email: str
    subtipo: str


class FuncionarioIn(BaseModel):
    cpf: str
    nome: str
    senha: str
    email: str
    tipo: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cpf": "12345678910",
                "nome": "John Doe",
                "senha": "John123!",
                "email": "john@doe.com",
                "tipo": "admin",
            }
        }
    )
