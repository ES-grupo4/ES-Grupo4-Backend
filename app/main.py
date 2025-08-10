from fastapi import FastAPI
from .routers.funcionario import funcionarios_router
from .routers.auth import auth_router
from .routers.compra import compra_router

from fastapi.middleware.cors import CORSMiddleware
from .routers.informacoes_gerais import informacoes_gerais_router
from .routers.cliente import cliente_router
from .models.db_setup import engine
from .models.models import Funcionario

from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from datetime import date


@asynccontextmanager
async def setUpAdmin(app: FastAPI):
    db = Session(engine)
    admin_data = {
        "cpf": "19896507406",
        "nome": "John Doe",
        "senha": "John123!",
        "email": "john@doe.com",
        "tipo": "admin",
        "data_entrada": date(2025, 8, 4),
    }

    admin_existente = db.query(Funcionario).filter_by(cpf=admin_data["cpf"]).first()
    if not admin_existente:
        admin = Funcionario(**admin_data)
        db.add(admin)
        db.commit()
    yield


# Só por enquanto
app = FastAPI(lifespan=setUpAdmin)

# =====================================
# Liberando acesso da api 
origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# =====================================

app.include_router(funcionarios_router)
app.include_router(informacoes_gerais_router)
app.include_router(auth_router)
app.include_router(compra_router)
app.include_router(cliente_router)
