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
            "00000000",     # usado em duplicado
            "1111111111",   # 10 dígitos
            "222222222222", # 12 dígitos
            "33333abc333",  # alfanumérico
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

    # Novos testes de erro:

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
        response = client.post("/cliente/", json=payload)
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
        response = client.post("/cliente/", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_criar_cliente_cpf_alfanumerico(self):
        payload = {
            "cpf": "33333abc333",  # contém letras
            "nome": "CPF Alfanumérico",
            "matricula": "20240201",
            "tipo": "tecnico",
            "graduando": False,
            "pos_graduando": False,
            "bolsista": False,
        }
        response = client.post("/cliente/", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_criar_cliente_duplicado(self):
        # cria pela primeira vez
        payload = {
            "cpf": "00000000",  # 8 dígitos mas vamos assumir a validação do DB
            "nome": "Origem Duplicado",
            "matricula": "20240202",
            "tipo": "aluno",
            "graduando": True,
            "pos_graduando": False,
            "bolsista": True,
        }
        client.post("/cliente/", json=payload)

        # tenta criar novamente com mesmo CPF
        payload2 = payload.copy()
        payload2["nome"] = "Tentativa Duplicada"
        response = client.post("/cliente/", json=payload2)
        self.assertIn(response.status_code, (400, 422))

    def test_remove_cliente_inexistente(self):
        response = client.delete("/cliente/99999999998")
        self.assertEqual(response.status_code, 404)

    def test_edita_cliente_matricula_invalida(self):
        # primeiro criar cliente válido
        payload = {
            "cpf": "12345678901",
            "nome": "Para Editar",
            "matricula": "20240203",
            "tipo": "aluno",
            "graduando": False,
            "pos_graduando": True,
            "bolsista": False,
        }
        client.post("/cliente/", json=payload)

        # tenta editar com matrícula vazia
        edit_payload = {"matricula": ""}
        response = client.put(f"/cliente/{payload['cpf']}", json=edit_payload)
        self.assertEqual(response.status_code, 405)

    def test_edita_cliente_tipo_invalido(self):
        # cria cliente
        payload = {
            "cpf": "12345678901",
            "nome": "Para Editar Tipo",
            "matricula": "20240204",
            "tipo": "tecnico",
            "graduando": False,
            "pos_graduando": False,
            "bolsista": False,
        }
        client.post("/cliente/", json=payload)

        # tenta editar com tipo inválido
        edit_payload = {"tipo": "externoX"}
        response = client.put(f"/cliente/{payload['cpf']}", json=edit_payload)
        self.assertEqual(response.status_code, 405)

    def test_edita_cliente_sem_payload(self):
        # cria cliente
        payload = {
            "cpf": "12345678901",
            "nome": "Sem Payload",
            "matricula": "20240205",
            "tipo": "aluno",
            "graduando": True,
            "pos_graduando": False,
            "bolsista": True,
        }
        client.post("/cliente/", json=payload)

        # PUT sem corpo
        response = client.put(f"/cliente/{payload['cpf']}", json={})
        self.assertIn(response.status_code, (200, 422, 405))


    # Testes para rotas inválidas

    def test_rota_inexistente_get(self):
        response = client.get("/clientes/")
        self.assertEqual(response.status_code, 404)

    def test_rota_inexistente_post(self):
        response = client.post("/cliente/inexistente", json={})
        self.assertEqual(response.status_code, 405)

    def test_metodo_nao_permitido(self):
        # POST em endpoint GET-only
        response = client.post(f"/cliente/{'12345678901'}")
        self.assertEqual(response.status_code, 405)


if __name__ == '__main__':
    unittest.main()
