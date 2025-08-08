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


class CompraIn(BaseModel):
    usuario_id: int
    horario: datetime
    local: str
    forma_pagamento: FormaPagamentoEnum
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "usuario_id": "1",
                "horario": "2025-04-12T10:50:00",
                "local": "humanas",
                "forma_pagamento": "pix",
            }
        }
    )
