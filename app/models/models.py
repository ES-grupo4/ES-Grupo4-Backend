from datetime import datetime, time, date
from sqlalchemy import ForeignKey, String, DateTime, JSON, Date, LargeBinary, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from enum import Enum as PyEnum
from ..core.seguranca import fernet


class ClienteTipo(PyEnum):
    externo = "externo"
    professor = "professor"
    aluno = "aluno"
    tecnico = "tecnico"


class FuncionarioTipo(PyEnum):
    admin = "admin"
    funcionario = "funcionario"


class FormaPagamentoCompra(PyEnum):
    credito = "credito"
    pix = "pix"
    debito = "debito"
    dinheiro = "dinheiro"


class Base(DeclarativeBase):
    pass


class Usuario(Base):
    __tablename__ = "usuario"

    cpf_hash: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    cpf_cript: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    nome: Mapped[str | None] = mapped_column(String(100), nullable=True)
    id: Mapped[int] = mapped_column(primary_key=True)
    subtipo: Mapped[str] = mapped_column(String())

    __mapper_args__ = {
        "polymorphic_on": subtipo,
    }

    def __repr__(self) -> str:
        return f"Usuario: {self.id=} {self.nome=} {self.subtipo}"

    def get_cpf(self, fernet):
        if not self.cpf_cript:
            return None
        return fernet.decrypt(self.cpf_cript).decode()


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

    @property
    def cpf(self):
        if not self.cpf_cript:
            return None
        return fernet.decrypt(self.cpf_cript).decode()


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
    info: Mapped[dict] = mapped_column(JSON)
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
