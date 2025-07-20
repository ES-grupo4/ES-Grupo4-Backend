import unittest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestInformacoesGerais(unittest.TestCase):
    def setUp(self):
        self.client = client
        # cria um registro se ele não existir
        payload = {
            "nome_empresa": "Empresa",
            "preco_almoco": 10,
            "preco_meia_almoco": 5,
            "preco_jantar": 14,
            "preco_meia_jantar": 7,
            "periodo_almoco": "2025-07-20T12:30:00",
            "periodo_jantar": "2025-07-20T19:00:00",
        }
        response = self.client.put("/informacoes-gerais/", json=payload)
        print("Status code:", response.status_code)
        print("Response body:", response.text)

    def test_update_informacoes_gerais(self):
        payload = {
            "nome_empresa": "Empresa Atualizada",
            "preco_almoco": 30,
            "preco_meia_almoco": 18,
            "preco_jantar": 35,
            "preco_meia_jantar": 20,
            "periodo_almoco": "2025-07-20T12:30:00",
            "periodo_jantar": "2025-07-20T19:00:00",
        }
        response = self.client.put("/informacoes-gerais/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["nome_empresa"] == "Empresa Atualizada"
        assert data["preco_jantar"] == 35

        response_check = client.get("/informacoes-gerais/")
        assert response_check.status_code == 200
        assert response_check.json()["nome_empresa"] == "Empresa Atualizada"
