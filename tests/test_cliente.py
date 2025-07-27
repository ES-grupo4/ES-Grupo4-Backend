import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.models.models import Cliente
from app.models.db_setup import bd_session

client = TestClient(app)


class ClienteTestCase(unittest.TestCase):
    def tearDown(self):
        # Cleanup genérico para qualquer CPF usado nos testes
        session = bd_session()
        cpfs_testados = [
            "12345678901",  # usado no setup/base
            "99999999999",  # usado no test_cria_cliente
            "00000000",  # usado em duplicado
        ]
        for cpf in cpfs_testados:
            cliente = session.query(Cliente).filter_by(cpf=cpf).first()
            if cliente:
                session.delete(cliente)
        session.commit()
        session.close()

    def test_cria_cliente(self):
        payload = {
            "cpf": "99999999999",
            "nome": "Cliente Independente",
            "matricula": "20249999",
            "tipo": "aluno",
            "graduando": False,
            "pos_graduando": True,
            "bolsista": False,
        }

        response = client.post("/cliente/", json=payload)
        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertEqual(data["cpf"], payload["cpf"])

    def test_busca_cliente_criado(self):
        payload = {
            "cpf": "12345678901",
            "nome": "Cliente Setup",
            "matricula": "20240001",
            "tipo": "aluno",
            "graduando": True,
            "pos_graduando": False,
            "bolsista": True,
        }
        client.post("/cliente/", json=payload)

        response = client.get(f"/cliente/{payload['cpf']}")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["cpf"], payload["cpf"])
        self.assertEqual(data["nome"], payload["nome"])

    def test_listar_clientes(self):
        payload = {
            "cpf": "12345678901",
            "nome": "Cliente Listar",
            "matricula": "20240002",
            "tipo": "aluno",
            "graduando": True,
            "pos_graduando": False,
            "bolsista": True,
        }
        client.post("/cliente/", json=payload)

        response = client.get("/cliente/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIsInstance(data, list)
        cpfs = [cliente["cpf"] for cliente in data]
        self.assertIn(payload["cpf"], cpfs)

    def test_remove_cliente(self):
        payload = {
            "cpf": "12345678901",
            "nome": "Cliente Remove",
            "matricula": "20240003",
            "tipo": "aluno",
            "graduando": True,
            "pos_graduando": False,
            "bolsista": True,
        }
        client.post("/cliente/", json=payload)

        # Remove
        response = client.delete(f"/cliente/{payload['cpf']}")
        self.assertEqual(response.status_code, 204)

        # Verifica que foi removido
        response = client.get(f"/cliente/{payload['cpf']}")
        self.assertEqual(response.status_code, 404)


    def test_criar_cliente_sem_campo_obrigatorio(self):
        payload = {
            "cpf": "12345678999",  # falta nome
            "matricula": "20240125",
            "tipo": "aluno",
            "graduando": True,
            "pos_graduando": False,
            "bolsista": False,
        }

        response = client.post("/cliente/", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_criar_cliente_com_tipo_invalido(self):
        payload = {
            "cpf": "12345678977",
            "nome": "Tipo Inválido",
            "matricula": "20240126",
            "tipo": "estagiario",  # tipo inválido
            "graduando": False,
            "pos_graduando": False,
            "bolsista": False,
        }

        response = client.post("/cliente/", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_criar_cliente_com_matricula_invalida(self):
        payload = {
            "cpf": "12345678988",
            "nome": "Cliente Matrícula Inválida",
            "matricula": "",  # campo inválido
            "tipo": "aluno",
            "graduando": True,
            "pos_graduando": False,
            "bolsista": False,
        }

        response = client.post("/cliente/", json=payload)
        self.assertEqual(response.status_code, 422)