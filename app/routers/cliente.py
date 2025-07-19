from fastapi import APIRouter, status, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.models import Cliente
from ..models.db_setup import conexao_bd
from ..schemas.cliente import ClienteIn, ClienteOut

cliente_router = APIRouter(
    prefix="/cliente",
    tags=["Cliente"],
)

@cliente_router.post(
    "/",
    summary="Cria um cliente",
    response_model=ClienteOut,
    status_code=status.HTTP_201_CREATED,
)
def cria_cliente(cliente: ClienteIn, db: conexao_bd):
    """
    Cria um cliente no sistema.
    """
    # Verifica se já existe um cliente com o mesmo CPF
    existing = db.scalar(select(Cliente).where(Cliente.cpf == cliente.cpf))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF já cadastrado"
        )

    novo = Cliente(
        cpf=cliente.cpf,
        nome=cliente.nome,
        matricula=cliente.matricula,
        tipo=cliente.tipo,
        graduando=cliente.graduando,
        pos_graduando=cliente.pos_graduando,
        bolsista=cliente.bolsista,
    )
    db.add(novo)
    db.flush()
    db.refresh(novo)
    return novo


@cliente_router.get(
    "/",
    summary="Pega todos os clientes", 
    response_model=list[ClienteOut]
)
def listar_clientes(db: conexao_bd):
    """
    Lista todos os clientes cadastrados.
    """
    clientes = db.scalars(select(Cliente)).all()
    return clientes