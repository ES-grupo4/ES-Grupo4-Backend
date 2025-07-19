from fastapi import FastAPI

from .routers.funcionario import funcionarios_router
from .routers.cliente import cliente_router


app = FastAPI()
app.include_router(funcionarios_router)
app.include_router(cliente_router)
