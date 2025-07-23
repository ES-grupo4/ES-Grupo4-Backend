from pydantic import BaseModel, ConfigDict


# coloquei LoginDTO porque LoginIn fica estranho
class LoginDTO(BaseModel):
    cpf: str
    senha: str

    model_config = ConfigDict(
        json_schema_extra={"example": {"cpf": "198.965.074-06", "senha": "John123!"}}
    )
