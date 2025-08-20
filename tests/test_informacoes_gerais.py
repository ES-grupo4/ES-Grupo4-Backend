import unittest
from datetime import date
from fastapi.testclient import TestClient
from app.main import app
from app.models.models import InformacoesGerais, Funcionario
from app.models.db_setup import engine
from app.core.seguranca import (
    gerar_hash,
    criptografa_cpf,
    descriptografa_cpf,
)
from datetime import time

from sqlalchemy.orm import Session

client = TestClient(app)


class TestInformacoesGerais(unittest.TestCase):
    def tearDown(self):
        self.db.query(InformacoesGerais).delete()
        self.db.commit()
        self.db.close()

    def setUp(self):
        self.client = client
        self.db: Session = Session(bind=engine)
        self.db.query(InformacoesGerais).delete()
        self.db.commit()

        info = InformacoesGerais(
            nome_empresa="Empresa",
            preco_almoco=10,
            preco_meia_almoco=5,
            preco_jantar=14,
            preco_meia_jantar=7,
            inicio_almoco=time(12, 30),
            fim_almoco=time(14, 0),
            inicio_jantar=time(19, 0),
            fim_jantar=time(20, 0),
        )
        self.db.add(info)
        self.db.commit()
        self.db.refresh(info)

        # Mockando um admin pra ter permissão nas rotas
        self.admin_data = {
            "cpf_hash": gerar_hash("19896507406"),
            "cpf_cript": criptografa_cpf("19896507406"),
            "nome": "John Doe",
            "senha": gerar_hash("John123!"),
            "email": "john@doe.com",
            "tipo": "admin",
            "data_entrada": date(2025, 8, 4),
        }

        admin_existente = (
            self.db.query(Funcionario)
            .filter_by(cpf_hash=self.admin_data["cpf_hash"])
            .first()
        )
        if not admin_existente:
            admin = Funcionario(**self.admin_data)
            self.db.add(admin)
            self.db.commit()

        login_payload = {
            "cpf": descriptografa_cpf(self.admin_data["cpf_cript"]),
            "senha": "John123!",
        }
        login_response = client.post("/auth/login", json=login_payload)
        assert login_response.status_code == 200, "Falha no login do admin"

        token = login_response.json().get("token")
        assert token, "Token não retornado no login"

        self.auth_headers = {"Authorization": f"Bearer {token}"}

    def test_update_informacoes_gerais(self):
        payload = {
            "nome_empresa": "Empresa Atualizada",
            "preco_almoco": 30,
            "preco_meia_almoco": 18,
            "preco_jantar": 35,
            "preco_meia_jantar": 20,
            "inicio_almoco": "12:30:00",
            "fim_almoco": "14:00:00",
            "inicio_jantar": "17:00:00",
            "fim_jantar": "20:00:00",
        }
        response = self.client.put(
            "/informacoes-gerais/", json=payload, headers=self.auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nome_empresa"] == "Empresa Atualizada"
        assert data["preco_jantar"] == 35
        self.tearDown()

    def test_get_informacoes_gerais(self):
        response = self.client.get("/informacoes-gerais/", headers=self.auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["nome_empresa"] == "Empresa"
        assert data["preco_almoco"] == 10
        assert data["preco_meia_almoco"] == 5
        assert data["preco_jantar"] == 14
        assert data["preco_meia_jantar"] == 7
        assert data["inicio_almoco"] == "12:30:00"
        assert data["fim_almoco"] == "14:00:00"
        assert data["inicio_jantar"] == "19:00:00"
        assert data["fim_jantar"] == "20:00:00"

    def test_get_informacoes_gerais_not_found(self):
        self.db.query(InformacoesGerais).delete()
        self.db.commit()
        self.tearDown()
        response = self.client.get("/informacoes-gerais/", headers=self.auth_headers)
        assert response.status_code == 404
        assert response.json() == {"detail": "Informações gerais não encontradas."}

    def test_update_informacoes_gerais_not_found(self):
        self.db.query(InformacoesGerais).delete()
        self.db.commit()
        payload = {
            "nome_empresa": "Empresa Atualizada",
            "preco_almoco": 30,
            "preco_meia_almoco": 18,
            "preco_jantar": 35,
            "preco_meia_jantar": 20,
            "inicio_almoco": "12:30:00",
            "fim_almoco": "14:00:00",
            "inicio_jantar": "17:00:00",
            "fim_jantar": "20:00:00",
        }
        response = self.client.put(
            "/informacoes-gerais/", json=payload, headers=self.auth_headers
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "404: Informações gerais não encontradas."}
