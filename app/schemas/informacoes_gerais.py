from pydantic import BaseModel
from datetime import datetime


class InformacoesGeraisResponse(BaseModel):
    id: int
    nome_empresa: str
    preco_almoco: int
    preco_meia_almoco: int
    preco_jantar: int
    preco_meia_jantar: int
    periodo_almoco: datetime
    periodo_jantar: datetime

    class Config:
        orm_mode = True


class InformacoesGeraisUpdate(BaseModel):
    nome_empresa: str
    preco_almoco: int
    preco_meia_almoco: int
    preco_jantar: int
    preco_meia_jantar: int
    periodo_almoco: datetime
    periodo_jantar: datetime
