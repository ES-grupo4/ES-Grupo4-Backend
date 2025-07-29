from pydantic import BaseModel, ConfigDict
from datetime import time

class InformacoesGeraisIn(BaseModel):
    nome_empresa: str
    preco_almoco: int
    preco_meia_almoco: int
    preco_jantar: int
    preco_meia_jantar: int
    periodo_almoco: time
    periodo_jantar: time

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome_empresa": "Fulano de Sal",
                "preco_almoco": 12,
                "preco_meia_almoco": 6,
                "preco_jantar": 10,
                "preco_meia_jantar": 5,
                "periodo_almoco": "10:30:00",
                "periodo_jantar": "17:00:00"
            }
        }
    )
