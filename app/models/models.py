from datetime import datetime, time, date
from sqlalchemy import ForeignKey, String, DateTime, JSON, Date, CHAR, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from enum import Enum as PyEnum


class ClienteTipo(PyEnum):
    EXTERNO = "externo"
    PROFESSOR = "professor"
    ALUNO = "aluno"
    TECNICO = "tecnico"


class FuncionarioTipo(PyEnum):
    ADMIN = "admin"
    FUNCIONARIO = "funcionario"


class FormaPagamentoCompra(PyEnum):
    CREDITO = "credito"
    PIX = "pix"
    DEBITO = "debito"
    DINHEIRO = "dinheiro"


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
    tipo: Mapped[FuncionarioTipo] = mapped_column(
        Enum(
            FuncionarioTipo,
            name="funcionario_tipo_enum",
            create_type=True,
            native_enum=True,
        )
    )
    senha: Mapped[str] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    data_entrada: Mapped[date] = mapped_column(Date)
    data_saida: Mapped[date | None] = mapped_column(Date, nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "funcionario",
    }


class Cliente(Usuario):
    __tablename__ = "cliente"

    usuario_id: Mapped[int] = mapped_column(ForeignKey(Usuario.id), primary_key=True)
    matricula: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tipo: Mapped[ClienteTipo] = mapped_column(
        Enum(ClienteTipo, name="cliente_tipo_enum", create_type=True, native_enum=True)
    )
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
    inicio_jantar: Mapped[time]
    inicio_almoco: Mapped[time]
    fim_jantar: Mapped[time]
    fim_almoco: Mapped[time]


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
    local: Mapped[str]
    forma_pagamento: Mapped[FormaPagamentoCompra] = mapped_column(
        Enum(
            FormaPagamentoCompra,
            name="forma_pagamento_enum",
            create_type=True,
            native_enum=True,
        )
    )
    horario: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
