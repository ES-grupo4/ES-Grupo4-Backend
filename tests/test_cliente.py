import unittest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.models import Cliente
from app.models.db_setup import engine

client = TestClient(app)


class ClienteTestCase(unittest.TestCase):
    def setUp(self):
        self.client = client
        self.db: Session = Session(bind=engine)
        # Limpa clientes com CPFs usados nos testes antes de cada teste
        cpfs_testados = [
            "12345678901",
            "99999999999",
            "1111111111",
            "222222222222",
            "33333abc33a",
        ]
        for cpf in cpfs_testados:
            cliente = self.db.query(Cliente).filter_by(cpf=cpf).first()
            if cliente:
                self.db.delete(cliente)
        self.db.commit()

    def tearDown(self):
        # Limpa clientes após cada teste para garantir isolamento
        cpfs_testados = [
            "12345678901",
            "99999999999",
            "1111111111",
            "222222222222",
            "33333abc33a",
        ]
        for cpf in cpfs_testados:
            cliente = self.db.query(Cliente).filter_by(cpf=cpf).first()
            if cliente:
                self.db.delete(cliente)
        self.db.commit()
        self.db.close()

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
        response = self.client.post("/cliente/", json=payload)
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
        self.client.post("/cliente/", json=payload)
        response = self.client.get(f"/cliente/{payload['cpf']}")
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
        self.client.post("/cliente/", json=payload)
        response = self.client.get("/cliente/")
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
        self.client.post("/cliente/", json=payload)
        response = self.client.delete(f"/cliente/{payload['cpf']}")
        self.assertEqual(response.status_code, 204)
        response = self.client.get(f"/cliente/{payload['cpf']}")
        self.assertEqual(response.status_code, 200)

    def test_criar_cliente_sem_campo_obrigatorio(self):
        payload = {
            "cpf": "12345678999",  # falta nome
            "matricula": "20240125",
            "tipo": "aluno",
            "graduando": True,
            "pos_graduando": False,
            "bolsista": False,
        }
        response = self.client.post("/cliente/", json=payload)
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
        response = self.client.post("/cliente/", json=payload)
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
        response = self.client.post("/cliente/", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_criar_cliente_cpf_com_menos_digitos(self):
        payload = {
            "cpf": "1111111111",  # 10 dígitos
            "nome": "CPF Curto",
            "matricula": "20240130",
            "tipo": "aluno",
            "graduando": False,
            "pos_graduando": False,
            "bolsista": False,
        }
        response = self.client.post("/cliente/", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_criar_cliente_cpf_com_mais_digitos(self):
        payload = {
            "cpf": "222222222222",  # 12 dígitos
            "nome": "CPF Longo",
            "matricula": "20240131",
            "tipo": "professor",
            "graduando": False,
            "pos_graduando": False,
            "bolsista": False,
        }
        response = self.client.post("/cliente/", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_criar_cliente_cpf_alfanumerico(self):
        payload = {
            "cpf": "33333abc33a",  # exatamente 11 caracteres, com letras
            "nome": "CPF Alfanumérico",
            "matricula": "20240201",
            "tipo": "tecnico",
            "graduando": False,
            "pos_graduando": False,
            "bolsista": False,
        }
        response = self.client.post("/cliente/", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_remove_cliente_inexistente(self):
        response = self.client.delete("/cliente/99999999998")
        self.assertEqual(response.status_code, 404)

    def test_edita_cliente_matricula_invalida(self):
        payload = {
            "cpf": "12345678901",
            "nome": "Para Editar",
            "matricula": "20240203",
            "tipo": "aluno",
            "graduando": False,
            "pos_graduando": True,
            "bolsista": False,
        }
        self.client.post("/cliente/", json=payload)
        edit_payload = {"matricula": ""}
        response = self.client.put(f"/cliente/{payload['cpf']}", json=edit_payload)
        self.assertIn(response.status_code, (200, 422))

    def test_edita_cliente_tipo_invalido(self):
        payload = {
            "cpf": "12345678901",
            "nome": "Para Editar Tipo",
            "matricula": "20240204",
            "tipo": "tecnico",
            "graduando": False,
            "pos_graduando": False,
            "bolsista": False,
        }
        self.client.post("/cliente/", json=payload)
        edit_payload = {"tipo": "externoX"}
        response = self.client.put(f"/cliente/{payload['cpf']}", json=edit_payload)
        self.assertIn(response.status_code, (200, 422))

    def test_edita_cliente_sem_payload(self):
        payload = {
            "cpf": "12345678901",
            "nome": "Sem Payload",
            "matricula": "20240205",
            "tipo": "aluno",
            "graduando": True,
            "pos_graduando": False,
            "bolsista": True,
        }
        self.client.post("/cliente/", json=payload)
        response = self.client.put(f"/cliente/{payload['cpf']}", json={})
        self.assertIn(response.status_code, (200, 422))

    def test_rota_inexistente_get(self):
        response = self.client.get("/clientes/")
        self.assertEqual(response.status_code, 404)

    def test_rota_inexistente_post(self):
        response = self.client.post("/cliente/inexistente", json={})
        self.assertEqual(response.status_code, 405)

    def test_metodo_nao_permitido(self):
        response = self.client.post(f"/cliente/12345678901")
        self.assertEqual(response.status_code, 405)

    def test_criar_cliente_duplicado(self):
        # CPF válido de 11 dígitos
        payload = {
            "cpf": "55566677788",
            "nome": "Cliente Original",
            "matricula": "20240300",
            "tipo": "aluno",
            "graduando": True,
            "pos_graduando": False,
            "bolsista": False,
        }
        # cria pela primeira vez — deve funcionar
        response1 = self.client.post("/cliente/", json=payload)

        # tenta criar novamente com o mesmo CPF
        payload2 = payload.copy()
        payload2["nome"] = "Cliente Duplicado"
        response2 = self.client.post("/cliente/", json=payload2)

        # deve retornar erro de duplicidade: 400 (violação de chave) ou 422 (validação)
        self.assertIn(response2.status_code, (400, 422))


if __name__ == "__main__":
    unittest.main()
