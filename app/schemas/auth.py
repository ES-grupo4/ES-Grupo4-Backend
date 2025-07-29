from pydantic import BaseModel, ConfigDict


# coloquei LoginDTO porque LoginIn fica estranho
class LoginDTO(BaseModel):
    cpf: str
    senha: str

    model_config = ConfigDict(
        json_schema_extra={"example": {"cpf": "12345678910", "senha": "John123!"}}
    )
