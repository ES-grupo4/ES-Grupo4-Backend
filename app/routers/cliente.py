from ..schemas.cliente import ClienteEdit
from fastapi import APIRouter, status, HTTPException
from sqlalchemy import select
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


@cliente_router.delete(
    "/{cpf}",
    summary="Remove um cliente pelo CPF",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remover_cliente(cpf: str, db: conexao_bd):
    """
    Remove um cliente do sistema a partir do CPF.
    """
    cliente = db.scalar(select(Cliente).where(Cliente.cpf == cpf))
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado"
        )

    db.delete(cliente)
    db.flush()


@cliente_router.patch(
    "/{cpf}",
    summary="Edita os dados de um cliente pelo CPF",
    response_model=ClienteOut,
)
def editar_cliente(cpf: str, dados: ClienteEdit, db: conexao_bd):
    """
    Edita os dados de um cliente existente, exceto CPF, ID e tipo.
    """
    cliente = db.scalar(select(Cliente).where(Cliente.cpf == cpf))
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado"
        )

    # Atualiza apenas os campos fornecidos
    for campo, valor in dados.dict(exclude_unset=True).items():
        setattr(cliente, campo, valor)

    db.flush()
    db.refresh(cliente)
    return cliente


@cliente_router.get(
    "/{cpf}",
    summary="Busca um cliente pelo CPF",
    response_model=ClienteOut,
)
def buscar_cliente(cpf: str, db: conexao_bd):
    """
    Retorna os dados de um cliente a partir do CPF.
    """
    cliente = db.scalar(select(Cliente).where(Cliente.cpf == cpf))
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado"
        )
    return cliente
