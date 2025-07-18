from datetime import datetime
from sqlalchemy import ForeignKey, String, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
  pass

class Usuario(Base):
  __tablename__ = "usuario"

  cpf: Mapped[str | None] = mapped_column(String(11))
  nome: Mapped[str | None]
  id: Mapped[int] = mapped_column(primary_key=True)
  subtipo: Mapped[str] = mapped_column(String())

  __mapper_args__ = {
    "polymorphic_identity": "usuario",
    "polymorphic_on": subtipo,
  }

class Funcionario(Usuario):
  __tablename__ = "funcionario"

  usuario_id: Mapped[int] = mapped_column(ForeignKey(Usuario.id), primary_key=True)
  subtipo: Mapped[str]
  senha: Mapped[str]
  email: Mapped[str | None]
    
  __mapper_args__ = {
    "polymorphic_identity": "funcionario",
  }

class Cliente(Usuario):
  __tablename__ = "cliente"

  usuario_id: Mapped[int] = mapped_column(ForeignKey(Usuario.id), primary_key=True)
  matricula: Mapped[str | None] 
  subtipo: Mapped[str]
  graduando: Mapped[bool]
  pos_graduando: Mapped[bool]
  bolsista: Mapped[bool]

  __mapper_args__ = {
    "polymorphic_identity": "cliente",
  }

class InformacoesGerais(Base):
  __tablename__ = "informacoes_gerais"

  id: Mapped[int] = mapped_column(primary_key=True)
  nome_empresa: Mapped[str]
  preco_almoco: Mapped[int]
  preco_meia_almoco: Mapped[int]
  preco_jantar: Mapped[int]
  preco_meia_jantar: Mapped[int]
  periodo_almoco: Mapped[datetime] = mapped_column(DateTime)
  periodo_jantar: Mapped[datetime] = mapped_column(DateTime)

class HistoricoAcoes(Base):
  __tablename__ = "historico_acoes"

  id: Mapped[int] = mapped_column(primary_key=True)
  usuario_id_ator: Mapped[int] = mapped_column(ForeignKey(Funcionario.usuario_id))
  usuario_id_alvo: Mapped[int] = mapped_column(ForeignKey(Cliente.usuario_id))
  informacoes_acao: Mapped[dict] = mapped_column(JSON)


class Compra(Base):
  __tablename__ = "compra"

  usuario_id: Mapped[int] = mapped_column(primary_key=True)
  local: Mapped[str] 
  forma_pagamento: Mapped[str]
  tipo_cliente: Mapped[str]


