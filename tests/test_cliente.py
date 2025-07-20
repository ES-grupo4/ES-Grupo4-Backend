import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.models.models import Cliente
from app.models.db_setup import bd_session

client = TestClient(app)

class ClienteTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.session = bd_session()

        # Remove apenas o cliente de CPF do setup, se existir
        cpf_setup = "12345678901"
        cls.session.query(Cliente).filter(Cliente.cpf == cpf_setup).delete()
        cls.session.commit()

        cls.setup_payload = {
            "cpf": cpf_setup,
            "nome": "Cliente Setup",
            "matricula": "20240001",
            "tipo": "aluno",
            "graduando": True,
            "pos_graduando": False,
            "bolsista": True
        }

        response = client.post("/cliente/", json=cls.setup_payload)
        cls.setup_response_data = response.json()
        cls.setup_status_code = response.status_code

    @classmethod
    def tearDownClass(cls):
        # Remove o cliente criado no setup
        cls.session.query(Cliente).filter(Cliente.cpf == cls.setup_payload["cpf"]).delete()
        cls.session.commit()
        cls.session.close()

    # ---------------------------------- #
    def test_cria_cliente(self):
        payload = {
            "cpf": "99999999999",
            "nome": "Cliente Independente",
            "matricula": "20249999",
            "tipo": "aluno",
            "graduando": False,
            "pos_graduando": True,
            "bolsista": False
        }

        response = client.post("/cliente/", json=payload)
        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertEqual(data["cpf"], payload["cpf"])
        self.assertEqual(data["nome"], payload["nome"])
        self.assertEqual(data["matricula"], payload["matricula"])
        self.assertEqual(data["tipo"], payload["tipo"])
        self.assertEqual(data["graduando"], payload["graduando"])
        self.assertEqual(data["pos_graduando"], payload["pos_graduando"])
        self.assertEqual(data["bolsista"], payload["bolsista"])
        self.assertIn("id", data)

        # Limpeza após o teste
        session = bd_session()
        session.query(Cliente).filter(Cliente.cpf == payload["cpf"]).delete()
        session.commit()
        session.close()

    # ---------------------------------- #
    def test_busca_cliente_criado_no_setup(self):
        cpf = self.setup_payload["cpf"]
        response = client.get(f"/cliente/{cpf}")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["cpf"], self.setup_payload["cpf"])
        self.assertEqual(data["nome"], self.setup_payload["nome"])
        self.assertEqual(data["matricula"], self.setup_payload["matricula"])
        self.assertEqual(data["tipo"], self.setup_payload["tipo"])
        self.assertEqual(data["graduando"], self.setup_payload["graduando"])
        self.assertEqual(data["pos_graduando"], self.setup_payload["pos_graduando"])
        self.assertEqual(data["bolsista"], self.setup_payload["bolsista"])
        self.assertIn("id", data)

    # ---------------------------------- #
    def test_listar_clientes(self):
        response = client.get("/cliente/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)

        cpfs = [cliente["cpf"] for cliente in data]
        self.assertIn(self.setup_payload["cpf"], cpfs)

    # ---------------------------------- #
    def test_remove_cliente(self):
        # Criar cliente temporário para remoção
        payload = {
            "cpf": "88888888888",
            "nome": "Cliente Removido",
            "matricula": "20248888",
            "tipo": "aluno",
            "graduando": False,
            "pos_graduando": False,
            "bolsista": False
        }
        client.post("/cliente/", json=payload)

        # Remove o cliente
        response = client.delete(f"/cliente/{payload['cpf']}")
        self.assertEqual(response.status_code, 204)

        # Tenta buscar o cliente removido, deve retornar 404
        response_busca = client.get(f"/cliente/{payload['cpf']}")
        self.assertEqual(response_busca.status_code, 404)

    # ---------------------------------- #
    def test_cria_cliente_com_cpf_duplicado(self):
        # Usa o CPF do cliente criado no setup para tentar criar novamente
        payload_duplicado = {
            "cpf": self.setup_payload["cpf"],
            "nome": "Outro Cliente",
            "matricula": "00000000",
            "tipo": "aluno",
            "graduando": False,
            "pos_graduando": False,
            "bolsista": False
        }

        response = client.post("/cliente/", json=payload_duplicado)
        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertIn("CPF já cadastrado", data.get("detail", ""))
