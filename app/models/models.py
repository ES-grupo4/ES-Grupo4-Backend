from datetime import datetime, time, date
from sqlalchemy import (
    ForeignKey,
    String,
    DateTime,
    JSON,
    Time,
    Date,
    Boolean,
    Integer,
    CHAR,
    func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Usuario(Base):
    __tablename__ = "usuario"

    cpf: Mapped[str | None] = mapped_column(CHAR(11), unique=True, nullable=True)
    nome: Mapped[str | None] = mapped_column(String(100), nullable=True)
    id: Mapped[int] = mapped_column(primary_key=True)
    subtipo: Mapped[str] = mapped_column(String())

    __mapper_args__ = {
        "polymorphic_on": subtipo,
        "polymorphic_abstract": True,
    }

    def __repr__(self) -> str:
        return f"Usuario: {self.id=} {self.cpf=} {self.nome=} {self.subtipo}"


class Funcionario(Usuario):
    __tablename__ = "funcionario"

    usuario_id: Mapped[int] = mapped_column(ForeignKey(Usuario.id), primary_key=True)
    tipo: Mapped[str] = mapped_column(String(50))
    senha: Mapped[str] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    data_entrada: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    data_saida: Mapped[date | None] = mapped_column(Date, nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "funcionario",
    }


class Cliente(Usuario):
    __tablename__ = "cliente"

    usuario_id: Mapped[int] = mapped_column(ForeignKey(Usuario.id), primary_key=True)
    matricula: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tipo: Mapped[str] = mapped_column(String(50))
    graduando: Mapped[bool] = mapped_column(Boolean)
    pos_graduando: Mapped[bool] = mapped_column(Boolean)
    bolsista: Mapped[bool] = mapped_column(Boolean)

    __mapper_args__ = {
        "polymorphic_identity": "cliente",
    }


class InformacoesGerais(Base):
    __tablename__ = "informacoes_gerais"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome_empresa: Mapped[str] = mapped_column(String())
    preco_almoco: Mapped[int] = mapped_column(Integer)
    preco_meia_almoco: Mapped[int] = mapped_column(Integer)
    preco_jantar: Mapped[int] = mapped_column(Integer)
    preco_meia_jantar: Mapped[int] = mapped_column(Integer)
    comeco_jantar: Mapped[time] = mapped_column(Time)
    comeco_almoco: Mapped[time] = mapped_column(Time)
    fim_jantar: Mapped[time] = mapped_column(Time)
    fim_almoco: Mapped[time] = mapped_column(Time)


class HistoricoAcoes(Base):
    __tablename__ = "historico_acoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id_ator: Mapped[int] = mapped_column(ForeignKey(Funcionario.usuario_id))
    usuario_id_alvo: Mapped[int] = mapped_column(ForeignKey(Cliente.usuario_id))
    informacoes_acao: Mapped[dict] = mapped_column(JSON)
    data: Mapped[datetime] = mapped_column(DateTime)


class Compra(Base):
    __tablename__ = "compra"

    usuario_id: Mapped[int] = mapped_column(ForeignKey(Usuario.id), primary_key=True)
    local: Mapped[str] = mapped_column(String())
    forma_pagamento: Mapped[str] = mapped_column(String(50))
    horario: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
