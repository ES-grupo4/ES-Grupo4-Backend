from fastapi import FastAPI
from app.routers import employees  # noqa: F401

from .routers.funcionario import funcionarios_router


app = FastAPI()
<<<<<<< HEAD

app.include_router(employees.router)

# Sempre preencham summary e tags
# Tags fazem sentido de ir nos APIRouter tmb
origins = [
    "http://localhost",
    "http://localhost:8000",
]


@app.get("/", summary="Te dá oi", tags=["Tag foda"])
def root():
    return {"message": "Hello world"}
=======
app.include_router(funcionarios_router)
>>>>>>> 10ac26230d211b7d7f2a76c001ee9bf305b6c26b
