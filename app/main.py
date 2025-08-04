from fastapi import FastAPI
from .routers.funcionario import funcionarios_router
from .routers.auth import auth_router
from .routers.informacoes_gerais import informacoes_gerais_router
from .routers.cliente import cliente_router

app = FastAPI()

app.include_router(funcionarios_router)
app.include_router(informacoes_gerais_router)
app.include_router(auth_router)
app.include_router(cliente_router)