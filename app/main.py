from fastapi import FastAPI
import uvicorn
from uvicorn.config import LOGGING_CONFIG

from app.core.seguranca import criptografa_cpf, gerar_hash
from .routers.funcionario import funcionarios_router
from .routers.auth import auth_router
from .routers.compra import compra_router
from .routers.relatorio import relatorio_router

from fastapi.middleware.cors import CORSMiddleware
from .routers.informacoes_gerais import informacoes_gerais_router

from .routers.cliente import cliente_router
from .routers.historico_acoes import acoes_router
from .models.db_setup import engine
from .models.models import Funcionario, InformacoesGerais

from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from datetime import date, time


@asynccontextmanager
async def setUp(app: FastAPI):
    db = Session(engine)
    senha = gerar_hash("John123!")
    cpf_hash = gerar_hash("19896507406")
    cpf_cript = criptografa_cpf("19896507406")
    admin_data = {
        "cpf_hash": cpf_hash,
        "cpf_cript": cpf_cript,
        "nome": "John Doe",
        "senha": senha,
        "email": "john@doe.com",
        "tipo": "admin",
        "data_entrada": date(2025, 8, 4),
    }
    admin_existente = (
        db.query(Funcionario).filter_by(cpf_hash=admin_data["cpf_hash"]).first()
    )
    if not admin_existente:
        admin = Funcionario(**admin_data)
        db.add(admin)
        db.commit()
    if not db.query(InformacoesGerais).first():
        info_gerais_data = {
            "nome_empresa": "RU sistema",
            "preco_almoco": 1200,
            "preco_meia_almoco": 600,
            "preco_jantar": 1000,
            "preco_meia_jantar": 500,
            "inicio_almoco": time(10, 30, 00),
            "fim_almoco": time(14, 00, 00),
            "inicio_jantar": time(17, 00, 00),
            "fim_jantar": time(20, 00, 00),
        }
        db.add(InformacoesGerais(**info_gerais_data))
        db.commit()

    yield


# Só por enquanto
app = FastAPI(
    lifespan=setUp,
    docs_url="/app/docs",
    openapi_url="/app/openapi.json",
)

# =====================================
# Liberando acesso da api
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# =====================================

app.include_router(auth_router)
app.include_router(acoes_router)
app.include_router(cliente_router)
app.include_router(compra_router)
app.include_router(funcionarios_router)
app.include_router(informacoes_gerais_router)
app.include_router(relatorio_router)


if __name__ == "__main__":
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = (
        "%(asctime)s [%(name)s] %(levelprefix)s %(message)s"
    )
    LOGGING_CONFIG["formatters"]["access"]["fmt"] = (
        '%(asctime)s [%(name)s] %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'
    )
    uvicorn.run(app, port=8000)
