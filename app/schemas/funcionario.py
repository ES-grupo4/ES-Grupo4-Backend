from pydantic import BaseModel, ConfigDict


class FuncionarioOut(BaseModel):
    id: int
    nome: str
    cpf: str
    email: str
    tipo: str


class FuncionarioIn(BaseModel):
    cpf: str
    nome: str
    senha: str
    email: str
    tipo: str

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
