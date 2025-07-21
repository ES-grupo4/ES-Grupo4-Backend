from fastapi import FastAPI
from .routers.funcionario import funcionarios_router
from .routers.auth import auth_router


app = FastAPI()

app.include_router(funcionarios_router)
app.include_router(auth_router)
