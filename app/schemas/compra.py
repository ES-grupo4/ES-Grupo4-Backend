from pydantic import BaseModel
from datetime import datetime, date, time


class CompraOut(BaseModel):
    horario: time
    dia: date
    refeicao: str
    local: str
    forma_pagamento: str
    comprador: str
    tipo_cliente: str


class CompraIn(BaseModel):
    usuario_id: str
    horario: datetime
    local: str
    forma_pagamento: str
    tipo_cliente: str
