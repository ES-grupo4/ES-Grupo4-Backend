from fastapi import FastAPI

from .routers.funcionario import funcionarios_router
from .routers.informacoes_gerais import informacoes_gerais_router

app = FastAPI()
app.include_router(funcionarios_router)
app.include_router(informacoes_gerais_router)
