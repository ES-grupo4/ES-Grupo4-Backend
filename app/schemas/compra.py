from fastapi import Form
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
