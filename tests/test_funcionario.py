import unittest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCase(unittest.TestCase):
    def test_base(self):
        response = client.post("/funcionario/1212313092/aaa")
        response = response.json()
        assert response["message"] == "Funcionário criado com sucesso"
