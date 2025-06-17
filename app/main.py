from fastapi import FastAPI

app = FastAPI()


# Sempre preencham summary e tags
# Tags fazem sentido de ir nos APIRouter tmb
@app.get("/", summary="Te dá oi", tags=["Tag foda"])
def root():
    return {"message": "Hello world"}
