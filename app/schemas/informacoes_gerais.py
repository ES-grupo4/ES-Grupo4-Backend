from pydantic import BaseModel, ConfigDict
from datetime import time


class InformacoesGeraisDTO(BaseModel):
    nome_empresa: str
    preco_almoco: int
    preco_meia_almoco: int
    preco_jantar: int
    preco_meia_jantar: int
    inicio_almoco: time
    fim_almoco: time
    inicio_jantar: time
    fim_jantar: time

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome_empresa": "Fulano de Sal",
                "preco_almoco": 12,
                "preco_meia_almoco": 6,
                "preco_jantar": 10,
                "preco_meia_jantar": 5,
                "inicio_almoco": "12:30:00",
                "fim_almoco": "14:00:00",
                "inicio_jantar": "17:00:00",
                "fim_jantar": "20:00:00",
            }
        },
        json_encoders={time: lambda t: t.strftime("%H:%M:%S")},
    )
