from fastapi import FastAPI
from app.routers import employees  # noqa: F401

app = FastAPI()

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
