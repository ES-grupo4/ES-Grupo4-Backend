from typing import List
from typing import Optional
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import JSON
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

class Base(DeclarativeBase):
    pass

class Usuario(Base):
    __tablename__ = "usuarios"

    cpf: Mapped[str] 
    nome: Mapped[str]
    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String)

    __mapper_args__ = {
        "polymorphic_identity": "usuarios",
        "polymorphic_on": tipo,
    }

class Funcionario(Usuario):
    __tablename__ = "funcionarios"

    usuario_id: Mapped[int] = mapped_column(ForeignKey(Usuario.id), primary_key=True)
    tipo: Mapped[str]
    senha: Mapped[str]
    email: Mapped[str]
    
    __mapper_args__ = {
        "polymorphic_identity": "funcionarios",
    }

class Cliente(Usuario):
    __tablename__ = "clientes"

    usuario_id: Mapped[int] = mapped_column(ForeignKey(Usuario.id), primary_key=True)
    matricula: Mapped[str]
    tipo: Mapped[str]
    graduando: Mapped[bool]
    pos_graduando: Mapped[bool]
    bolsista: Mapped[bool]

    __mapper_args__ = {
        "polymorphic_identity": "clientes",
    }

class Informacoes_Gerais(Base):
    __tablename__ = "informacoes_gerais"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome_empresa: Mapped[str]
    preco_almoco: Mapped[int]
    preco_meia_almoco: Mapped[int]
    preco_jantar: Mapped[int]
    preco_meia_jantar: Mapped[int]
    periodo_almoco: Mapped[datetime] = mapped_column(DateTime)
    periodo_jantar: Mapped[datetime] = mapped_column(DateTime)

class Historico_Acoes(Base):
    __tablename__ = "historico_acoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id_ator: Mapped[int] = mapped_column(ForeignKey(Funcionario.usuario_id))
    usuario_id_alvo: Mapped[int] = mapped_column(ForeignKey(Cliente.usuario_id))
    informacoes_acao: Mapped[dict] = mapped_column(JSON)


class Compra(Base):
    __tablename__ = "compras"

    usuario_id: Mapped[str] = mapped_column(primary_key=True)
    local: Mapped[str] 
    forma_pagamento: Mapped[str]
    tipo_cliente: Mapped[str]


