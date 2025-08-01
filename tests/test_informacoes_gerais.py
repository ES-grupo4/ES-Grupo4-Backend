import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.models.models import InformacoesGerais
from app.models.db_setup import engine
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
            periodo_almoco=time(12, 30),
            periodo_jantar=time(19, 0),
        )
        self.db.add(info)
        self.db.commit()
        self.db.refresh(info)

    def test_update_informacoes_gerais(self):
        payload = {
            "nome_empresa": "Empresa Atualizada",
            "preco_almoco": 30,
            "preco_meia_almoco": 18,
            "preco_jantar": 35,
            "preco_meia_jantar": 20,
            "periodo_almoco": "12:30:00",
            "periodo_jantar": "19:00:00",
        }
        response = self.client.put("/informacoes-gerais/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["nome_empresa"] == "Empresa Atualizada"
        assert data["preco_jantar"] == 35
        self.tearDown()

    def test_get_informacoes_gerais(self):
        response = self.client.get("/informacoes-gerais/")
        assert response.status_code == 200
        data = response.json()
        assert data["nome_empresa"] == "Empresa"
        assert data["preco_almoco"] == 10
        assert data["preco_meia_almoco"] == 5
        assert data["preco_jantar"] == 14
        assert data["preco_meia_jantar"] == 7
        assert data["periodo_almoco"] == "12:30:00"
        assert data["periodo_jantar"] == "19:00:00"

    def test_get_informacoes_gerais_not_found(self):
        self.db.query(InformacoesGerais).delete()
        self.db.commit()
        self.tearDown()
        response = self.client.get("/informacoes-gerais/")
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
            "periodo_almoco": "12:30:00",
            "periodo_jantar": "19:00:00",
        }
        response = self.client.put("/informacoes-gerais/", json=payload)
        assert response.status_code == 404
        assert response.json() == {"detail": "404: Informações gerais não encontradas."}
