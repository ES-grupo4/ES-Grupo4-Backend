from datetime import datetime
from typing import Annotated, Any
from pydantic import BaseModel, ConfigDict, StringConstraints


class AcaoOut(BaseModel):
    id: int
    acao: str
    data: datetime

    ator_id: int
    ator_nome: str
    ator_cpf: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=11, max_length=11)
    ]

    alvo_id: int | None = None
    alvo_nome: str | None = None
    alvo_cpf: Annotated[
        str | None,
        StringConstraints(strip_whitespace=True, min_length=11, max_length=11),
    ]

    info_adicional: dict[str, Any] | None = None


class AcaoPaginationOut(BaseModel):
    total_in_page: int
    page: int
    page_size: int
    total_pages: int
    items: list[AcaoOut]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_in_page": 2,
                "page": 1,
                "page_size": 10,
                "total_pages": 1,
                "items": [
                    {
                        "id": 1,
                        "ator_id": 1,
                        "ator_nome": "John Doe",
                        "ator_cpf": "19896507406",
                        "acao": "cadastrou cliente",
                        "alvo_id": 2,
                        "alvo_nome": "Cunoesse",
                        "alvo_cpf": "11122233344487",
                        "data": "2025-08-24T18:18:52.363935",
                        "info_adicional": None,
                    },
                    {
                        "id": 463,
                        "ator_id": 1,
                        "ator_nome": "John Doe",
                        "ator_cpf": "19896507406",
                        "acao": "cadastrou compra",
                        "alvo_id": None,
                        "alvo_nome": None,
                        "alvo_cpf": None,
                        "data": "2025-08-24T18:36:03.597823",
                        "info_adicional": '{"usuario_id":1,"horario":"2025-04-12T10:50:00","local":"humanas","forma_pagamento":"pix"}',
                    },
                ],
            }
        }
    )
