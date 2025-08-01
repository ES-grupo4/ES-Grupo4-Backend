from pydantic import BaseModel
from datetime import datetime


class CompraOut(BaseModel):
    usuario_id: str
    horario: datetime
    local: str
    forma_pagamento: str


class CompraIn(BaseModel):
    usuario_id: str
    horario: datetime
    local: str
    forma_pagamento: str
