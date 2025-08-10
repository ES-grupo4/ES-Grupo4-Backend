from datetime import date
import unittest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.models import Funcionario
from app.models.db_setup import engine

client = TestClient(app)


class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.db = Session(engine)
        self.funcionario_data = {
            "cpf": "12345678900",
            "nome": "John Doe",
            "senha": "John123!",
            "email": "john@doe.com",
            "tipo": "ADMIN",
            "data_entrada": date(2025, 8, 4),
        }

        funcionario_existente = (
            self.db.query(Funcionario)
            .filter_by(cpf=self.funcionario_data["cpf"])
            .first()
        )
        if not funcionario_existente:
            funcionario = Funcionario(**self.funcionario_data)
            self.db.add(funcionario)
            self.db.commit()

    def tearDown(self):
        funcionario = (
            self.db.query(Funcionario)
            .filter_by(cpf=self.funcionario_data["cpf"])
            .first()
        )
        if funcionario:
            self.db.delete(funcionario)
            self.db.commit()
        self.db.close()

    def test_login_sucesso(self):
        payload = {
            "cpf": self.funcionario_data["cpf"],
            "senha": self.funcionario_data["senha"],
        }
        response = client.post("/auth/login", json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("token", data)
        self.assertIsInstance(data["token"], str)

    def test_login_falha_senha_errada(self):
        payload = {"cpf": self.funcionario_data["cpf"], "senha": "abacaxi123"}
        response = client.post("/auth/login", json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Usuário ou senha incorretos")

    def test_login_usuario_inexistente(self):
        payload = {"cpf": "00000000000", "senha": "senha123"}
        response = client.post("/auth/login", json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Usuário ou senha incorretos")
