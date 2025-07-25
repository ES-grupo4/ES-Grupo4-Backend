from pydantic import BaseModel
from datetime import datetime

class InformacoesGeraisIn(BaseModel):
    nome_empresa: str
    preco_almoco: int
    preco_meia_almoco: int
    preco_jantar: int
    preco_meia_jantar: int
    periodo_almoco: datetime
    periodo_jantar: datetime

