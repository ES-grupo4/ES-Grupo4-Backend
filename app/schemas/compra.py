from enum import Enum
from pydantic import BaseModel
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


class CompraIn(BaseModel):
    usuario_id: int
    horario: datetime
    local: str
    forma_pagamento: FormaPagamentoEnum


class CompraPaginationOut(BaseModel):
    total_in_page: int
    page: int
    total_pages: int
    items: list[CompraOut]
