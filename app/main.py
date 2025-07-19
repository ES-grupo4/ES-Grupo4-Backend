from fastapi import FastAPI

from .routers.funcionario import funcionarios_router


app = FastAPI()
app.include_router(funcionarios_router)
