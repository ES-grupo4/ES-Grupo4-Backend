from fastapi import FastAPI
from app.routers import employees  # noqa: F401

from .routers.funcionario import funcionarios_router


app = FastAPI()
app.include_router(funcionarios_router)
