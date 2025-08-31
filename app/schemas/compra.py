from enum import Enum
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class FormaPagamentoEnum(str, Enum):
    pix = "pix"
    credito = "credito"
    debito = "debito"
    dinheiro = "dinheiro"


class CompraOut(BaseModel):
    usuario_id: int
    horario: datetime
    local: str
    forma_pagamento: str
    preco_compra: int

    class Config:
        from_attributes = True


class CompraPaginationOut(BaseModel):
    total_in_page: int
    page: int
    page_size: int
    total_pages: int
    items: list[CompraOut]


class CompraIn(BaseModel):
    usuario_id: int
    horario: datetime
    local: str
    forma_pagamento: FormaPagamentoEnum
    preco_compra: int
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "usuario_id": "1",
                "horario": "2025-04-12T10:50:00",
                "local": "humanas",
                "forma_pagamento": "pix",
                "preco_compra": 598,
            }
        }
    )
