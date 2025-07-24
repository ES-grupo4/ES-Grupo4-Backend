from fastapi import FastAPI
from .routers.funcionario import funcionarios_router
from .routers.auth import auth_router
from .routers.compra import compra_router


app = FastAPI()

app.include_router(funcionarios_router)
app.include_router(auth_router)
app.include_router(compra_router)
