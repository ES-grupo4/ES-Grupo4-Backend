from datetime import date
import unittest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.models import Funcionario
from app.models.db_setup import engine

client = TestClient(app)


class FuncionarioTestCase(unittest.TestCase):
    def setUp(self):
        self.db = Session(engine)
        # Mockando um admin pra ter permissão nas rotas
        self.admin_data = {
            "cpf": "19896507406",
            "nome": "John Doe",
            "senha": "John123!",
            "email": "john@doe.com",
            "tipo": "admin",
            "data_entrada": date(2025, 8, 4),
        }

        admin_existente = (
            self.db.query(Funcionario).filter_by(cpf=self.admin_data["cpf"]).first()
        )
        if not admin_existente:
            admin = Funcionario(**self.admin_data)
            self.db.add(admin)
            self.db.commit()

        login_payload = {
            "cpf": self.admin_data["cpf"],
            "senha": self.admin_data["senha"],
        }
        login_response = client.post("/auth/login", json=login_payload)
        assert login_response.status_code == 200, "Falha no login do admin"

        token = login_response.json().get("token")
        assert token, "Token não retornado no login"

        self.auth_headers = {"Authorization": f"Bearer {token}"}

        # Mockando um funcionario padrão pra evitar repetição de payload
        self.funcionario_padrao = {
            "cpf": "79920205451",
            "nome": "John Dois",
            "senha": "John123!",
            "email": "john@dois.com",
            "tipo": "funcionario",
            "data_entrada": "2025-08-04",
        }

    def tearDown(self):
        for cpf in ["19896507406", "79920205451", "89159073454"]:
            funcionario = self.db.query(Funcionario).filter_by(cpf=cpf).first()
            if funcionario:
                self.db.delete(funcionario)
                self.db.commit()
        self.db.close()

    def cria_funcionario(self, dados=None):
        dados = dados or self.funcionario_padrao
        response = client.post("/funcionario/", json=dados, headers=self.auth_headers)
        return response

    def busca_funcionario_por_cpf(self, cpf):
        response = client.get(f"/funcionario/?cpf={cpf}", headers=self.auth_headers)
        return response

    def test_cadastro_funcionario_sucesso(self):
        response = self.cria_funcionario()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Funcionário cadastrado com sucesso", response.text)

    def test_cadastro_funcionario_cpf_invalido(self):
        self.funcionario_padrao["cpf"] = "12345678910"
        response = self.cria_funcionario()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "CPF inválido")

    def test_cadastro_funcionario_cpf_duplicado(self):
        # cria uma vez
        response1 = self.cria_funcionario()
        self.assertEqual(response1.status_code, 200)

        # tenta criar de novo com mesmo CPF
        response2 = self.cria_funcionario()
        self.assertEqual(response2.status_code, 409)
        self.assertEqual(response2.json()["detail"], "CPF já cadastrado no sistema")

    def test_cadastro_funcionario_email_duplicado(self):
        # cria uma vez
        response1 = self.cria_funcionario()
        self.assertEqual(response1.status_code, 200)

        # tenta criar de novo com mesmo email e um CPF diferente
        self.funcionario_padrao["cpf"] = "89159073454"
        response2 = self.cria_funcionario()
        self.assertEqual(response2.status_code, 409)
        self.assertEqual(response2.json()["detail"], "Email já cadastrado no sistema")

    def test_cadastro_funcionario_email_invalido(self):
        self.funcionario_padrao["email"] = "emailfalso.com"
        response = self.cria_funcionario()
        self.assertEqual(response.status_code, 422)

        erro = response.json()
        self.assertIn("detail", erro)
        self.assertTrue(
            any(
                d.get("ctx", {}).get("reason")
                == "An email address must have an @-sign."
                for d in erro["detail"]
            ),
            "O erro não é de email inválido",
        )

    def test_atualiza_funcionario_com_sucesso(self):
        self.cria_funcionario()
        funcionario = self.busca_funcionario_por_cpf("79920205451").json()[0]
        payload = {
            "nome": "Fulaninho Games",
            "senha": "Jorginho123",
            "email": "novoemail@email.com",
            "tipo": "funcionario",
        }
        response = client.put(
            f"/funcionario/{funcionario['id']}/",
            json=payload,
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_funcionario_por_cpf("79920205451").json()[0], response.json()
        )

    def test_atualiza_funcionario_id_inexistente(self):
        self.cria_funcionario()
        payload = {
            "nome": "Fulaninho Games",
            "senha": "Jorginho123",
            "email": "novoemail@email.com",
            "tipo": "funcionario",
        }
        response = client.put(
            "/funcionario/99999/",
            json=payload,
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual("Funcionário não encontrado", response.json()["detail"])

    def test_atualiza_funcionario_sem_nome(self):
        self.cria_funcionario()
        funcionario = self.busca_funcionario_por_cpf("79920205451").json()[0]
        payload = {
            "senha": "Jorginho123",
            "email": "novoemail@email.com",
            "tipo": "funcionario",
        }

        response = client.put(
            f"/funcionario/{funcionario['id']}/",
            json=payload,
            headers=self.auth_headers,
        )

        payload_esperado = {
            "cpf": funcionario["cpf"],
            "nome": funcionario["nome"],
            "email": "novoemail@email.com",
            "tipo": "funcionario",
            "data_entrada": str(date.today()),
        }

        self.assertEqual(response.status_code, 200)
        for campo, valor in payload_esperado.items():
            self.assertEqual(response.json()[campo], valor)

    def test_atualiza_funcionario_sem_senha(self):
        self.cria_funcionario()
        funcionario = self.busca_funcionario_por_cpf("79920205451").json()[0]
        payload = {
            "nome": "Fulaninho Games",
            "email": "novoemail@email.com",
            "tipo": "funcionario",
        }

        response = client.put(
            f"/funcionario/{funcionario['id']}/",
            json=payload,
            headers=self.auth_headers,
        )

        payload_esperado = {
            "cpf": funcionario["cpf"],
            "nome": "Fulaninho Games",
            "email": "novoemail@email.com",
            "tipo": "funcionario",
            "data_entrada": str(date.today()),
        }

        self.assertEqual(response.status_code, 200)
        for campo, valor in payload_esperado.items():
            self.assertEqual(response.json()[campo], valor)

    def test_atualiza_funcionario_sem_email(self):
        self.cria_funcionario()
        funcionario = self.busca_funcionario_por_cpf("79920205451").json()[0]
        payload = {
            "nome": "Fulaninho Games",
            "senha": "Jorginho123",
            "tipo": "funcionario",
        }

        response = client.put(
            f"/funcionario/{funcionario['id']}/",
            json=payload,
            headers=self.auth_headers,
        )

        payload_esperado = {
            "cpf": funcionario["cpf"],
            "nome": "Fulaninho Games",
            "email": funcionario["email"],
            "tipo": "funcionario",
            "data_entrada": str(date.today()),
        }

        self.assertEqual(response.status_code, 200)
        for campo, valor in payload_esperado.items():
            self.assertEqual(response.json()[campo], valor)

    def test_atualiza_funcionario_sem_tipo(self):
        self.cria_funcionario()
        funcionario = self.busca_funcionario_por_cpf("79920205451").json()[0]
        payload = {
            "nome": "Fulaninho Games",
            "senha": "Jorginho123",
            "email": "novoemail@email.com",
        }

        response = client.put(
            f"/funcionario/{funcionario['id']}/",
            json=payload,
            headers=self.auth_headers,
        )

        payload_esperado = {
            "cpf": funcionario["cpf"],
            "nome": "Fulaninho Games",
            "email": "novoemail@email.com",
            "tipo": funcionario["tipo"],
            "data_entrada": str(date.today()),
        }

        self.assertEqual(response.status_code, 200)
        for campo, valor in payload_esperado.items():
            self.assertEqual(response.json()[campo], valor)

    def test_atualiza_funcionario_payload_vazio(self):
        self.cria_funcionario()
        funcionario = self.busca_funcionario_por_cpf("79920205451").json()[0]
        payload = {}

        response = client.put(
            f"/funcionario/{funcionario['id']}/",
            json=payload,
            headers=self.auth_headers,
        )

        payload_esperado = {
            "cpf": funcionario["cpf"],
            "nome": funcionario["nome"],
            "email": funcionario["email"],
            "tipo": funcionario["tipo"],
            "data_entrada": str(date.today()),
        }

        self.assertEqual(response.status_code, 200)
        for campo, valor in payload_esperado.items():
            self.assertEqual(response.json()[campo], valor)

    def test_atualiza_funcionario_email_invalido(self):
        self.cria_funcionario()
        funcionario = self.busca_funcionario_por_cpf("79920205451").json()[0]
        payload = {"email": "emailinvalido.com"}

        response = client.put(
            f"/funcionario/{funcionario['id']}/",
            json=payload,
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, 422)

        erro = response.json()
        self.assertIn("detail", erro)
        self.assertTrue(
            any(
                d.get("ctx", {}).get("reason")
                == "An email address must have an @-sign."
                for d in erro["detail"]
            ),
            "O erro não é de email inválido",
        )

    def test_atualiza_funcionario_tipo_invalido(self):
        self.cria_funcionario()
        funcionario = self.busca_funcionario_por_cpf("79920205451").json()[0]
        payload = {"tipo": "cliente"}

        response = client.put(
            f"/funcionario/{funcionario['id']}/",
            json=payload,
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, 422)

        erro = response.json()
        self.assertIn("detail", erro)
        self.assertTrue(
            any(
                d.get("ctx", {}).get("expected") == "'funcionario' or 'admin'"
                for d in erro["detail"]
            ),
            "O erro não é de tipo inválido",
        )

    def test_busca_funcionarios_sem_funcionarios(self):
        # Deixa a tabela de funcionarios vazia
        self.tearDown()
        response = client.get("/funcionario/", headers=self.auth_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([], response.json())

    def test_busca_funcionarios_sem_parametros(self):
        self.cria_funcionario()
        response = client.get("/funcionario/", headers=self.auth_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            self.busca_funcionario_por_cpf("79920205451").json()[0], response.json()
        )
        self.assertIn(
            self.busca_funcionario_por_cpf("19896507406").json()[0], response.json()
        )

    def test_busca_funcionarios_por_id(self):
        self.cria_funcionario()
        funcionario = self.busca_funcionario_por_cpf("79920205451").json()[0]
        response = client.get(
            f"/funcionario/?id={funcionario['id']}", headers=self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_funcionario_por_cpf("79920205451").json(), response.json()
        )

    def test_busca_funcionarios_por_id_inexistente(self):
        self.cria_funcionario()
        response = client.get("/funcionario/?id=9999", headers=self.auth_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([], response.json())

    def test_busca_funcionarios_por_cpf(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/?cpf=79920205451", headers=self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_funcionario_por_cpf("79920205451").json(), response.json()
        )

    def test_busca_funcionarios_por_cpf_inexistente(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/?cpf=12345678910", headers=self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([], response.json())

    def test_busca_funcionarios_por_nome(self):
        self.funcionario_padrao["nome"] = "Joao"
        self.cria_funcionario()
        response = client.get("/funcionario/?nome=Joao", headers=self.auth_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_funcionario_por_cpf("79920205451").json(), response.json()
        )

    def test_busca_funcionarios_por_nome_inexistente(self):
        self.funcionario_padrao["nome"] = "Jose"
        self.cria_funcionario()
        response = client.get("/funcionario/?nome=Joao", headers=self.auth_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([], response.json())

    def test_busca_funcionarios_por_email(self):
        self.funcionario_padrao["nome"] = "Joao"
        self.cria_funcionario()
        response = client.get("/funcionario/?nome=Joao", headers=self.auth_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_funcionario_por_cpf("79920205451").json(), response.json()
        )

    def test_busca_funcionarios_por_email_inexistente(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/?email=john@tres.com", headers=self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([], response.json())

    def test_busca_funcionarios_por_tipo_funcionario(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/?tipo=funcionario", headers=self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_funcionario_por_cpf("79920205451").json(), response.json()
        )

    def test_busca_funcionarios_por_tipo_admin(self):
        self.cria_funcionario()
        response = client.get("/funcionario/?tipo=admin", headers=self.auth_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_funcionario_por_cpf("19896507406").json(), response.json()
        )

    def test_busca_funcionarios_por_tipo_invalido(self):
        self.cria_funcionario()
        response = client.get("/funcionario/?tipo=cliente", headers=self.auth_headers)

        self.assertEqual(response.status_code, 422)

        erro = response.json()
        self.assertIn("detail", erro)
        self.assertTrue(
            any(
                d.get("ctx", {}).get("expected") == "'funcionario' or 'admin'"
                for d in erro["detail"]
            ),
            "O erro não é de tipo inválido",
        )

    def test_busca_funcionarios_por_data_entrada(self):
        self.cria_funcionario()
        response = client.get("/funcionario/?data_entrada=2025-08-04")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            self.busca_funcionario_por_cpf("19896507406").json()[0], response.json()
        )
        self.assertNotIn(
            self.busca_funcionario_por_cpf("79920205451").json()[0], response.json()
        )

    def test_busca_funcionarios_por_data_entrada_inexistente(self):
        self.cria_funcionario()
        response = client.get("/funcionario/?data_entrada=2005-02-13")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([], response.json())

    def test_busca_funcionarios_por_data_saida(self):
        self.cria_funcionario()
        data_saida = date.today()
        client.post(
            f"/funcionario/79920205451/desativar?data_saida={data_saida}",
            headers=self.auth_headers,
        )

        response = client.get(f"/funcionario/?data_saida={data_saida}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_funcionario_por_cpf("79920205451").json(), response.json()
        )
        self.assertIsNone(
            self.busca_funcionario_por_cpf("79920205451").json()[0]["email"]
        )

    def test_busca_funcionarios_por_data_saida_inexistente(self):
        self.cria_funcionario()
        data_saida = date.today()
        response = client.get(f"/funcionario/?data_saida={data_saida}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([], response.json())

    def test_deleta_funcionario_com_sucesso(self):
        self.cria_funcionario()
        response = client.delete(
            "/funcionario/?cpf=79920205451", headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Funcionário deletado com sucesso", response.text)

    def test_deleta_funcionario_cpf_inexistente(self):
        self.cria_funcionario()
        response = client.delete(
            "/funcionario/?cpf=80799286575", headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("Funcionário não encontrado", response.text)

    def test_desativa_funcionario_com_sucesso(self):
        self.cria_funcionario()
        data_saida = date.today()
        response = client.post(
            f"/funcionario/79920205451/desativar?data_saida={data_saida}",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Funcionário desativado com sucesso", response.text)

    def test_desativa_funcionario_cpf_inexistente(self):
        self.cria_funcionario()
        data_saida = date.today()
        response = client.post(
            f"/funcionario/80799286575/desativar?data_saida={data_saida}",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("Funcionário não encontrado", response.text)
