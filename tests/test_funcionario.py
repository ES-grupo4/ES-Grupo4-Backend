from datetime import date
import unittest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.seguranca import (
    criptografa_cpf,
    descriptografa_cpf,
    gerar_hash,
)
from app.main import app
from app.models.models import Funcionario
from app.models.db_setup import engine

client = TestClient(app)


class FuncionarioTestCase(unittest.TestCase):
    def setUp(self):
        self.db = Session(engine)
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
        self.auth_headers_invalido = {"Authorization": "Bearer token_invalido"}

        # Mockando um funcionario padrão pra evitar repetição de payload
        self.funcionario_padrao = {
            "cpf": "79920205451",
            "nome": "John Dois",
            "senha": "John123!",
            "email": "john@dois.com",
            "tipo": "funcionario",
            "data_entrada": "2025-08-22",
        }

    def tearDown(self):
        for cpf in ["19896507406", "79920205451", "89159073454"]:
            funcionario = (
                self.db.query(Funcionario).filter_by(cpf_hash=gerar_hash(cpf)).first()
            )
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

    def busca_admin_por_cpf(self, cpf):
        response = client.get(
            f"/funcionario/admin/?cpf={cpf}", headers=self.auth_headers
        )
        return response

    def login_funcionario(self):
        self.db = Session(engine)
        # Logando um funcionario inserido em cria_funcionario pra ter permissão nas rotas
        login_payload = {
            "cpf": "79920205451",
            "senha": "John123!",
        }
        login_response = client.post("/auth/login", json=login_payload)
        assert login_response.status_code == 200, "Falha no login do funcionario"

        token = login_response.json().get("token")
        assert token, "Token não retornado no login"

        self.auth_headers_funcionario = {"Authorization": f"Bearer {token}"}

    def test_cadastro_funcionario_sucesso(self):
        response = self.cria_funcionario()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Funcionário cadastrado com sucesso", response.text)

    def test_cadastro_funcionario_sem_autorizacao(self):
        self.cria_funcionario()
        self.login_funcionario()

        funcionario_data = {
            "cpf": "89159073454",
            "nome": "John Tres",
            "senha": "John123!",
            "email": "john@tres.com",
            "tipo": "funcionario",
            "data_entrada": "2025-08-04",
        }

        response = client.post(
            "/funcionario/",
            json=funcionario_data,
            headers=self.auth_headers_funcionario,
        )
        self.assertEqual(response.status_code, 403)

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
        # Cria funcionário padrão
        self.cria_funcionario()

        # Busca o funcionário criado
        funcionario = self.busca_funcionario_por_cpf("79920205451").json()["items"][0]

        # Payload com dados de atualização
        payload = {
            "nome": "Fulaninho Games",
            "senha": "Jorginho123",
            "email": "novoemail@email.com",
            "tipo": "funcionario",
        }

        # Atualiza o funcionário
        response = client.put(
            f"/funcionario/{funcionario['id']}/",
            json=payload,
            headers=self.auth_headers,
        )

        # Verifica se o status code é 200
        self.assertEqual(response.status_code, 200)

        # Verifica se os dados atualizados correspondem ao esperado
        funcionario_atualizado = self.busca_funcionario_por_cpf("79920205451").json()[
            "items"
        ][0]
        self.assertEqual(funcionario_atualizado, response.json())

    def test_atualiza_funcionario_sem_autorizacao(self):
        # Cria um funcionário e faz login com outro usuário
        self.cria_funcionario()
        self.login_funcionario()

        # Cria um segundo funcionário que será o alvo da atualização
        funcionario_data = {
            "cpf": "89159073454",
            "nome": "John Tres",
            "senha": "John123!",
            "email": "john@tres.com",
            "tipo": "funcionario",
            "data_entrada": "2025-08-04",
        }
        self.cria_funcionario(funcionario_data)

        # Busca o funcionário recém-criado
        funcionario = self.busca_funcionario_por_cpf("89159073454").json()["items"][0]

        # Payload de atualização
        payload = {
            "nome": "Fulaninho Games",
            "senha": "Jorginho123",
            "email": "novoemail@email.com",
            "tipo": "funcionario",
        }

        # Tenta atualizar usando credenciais sem permissão
        response = client.put(
            f"/funcionario/{funcionario['id']}/",
            json=payload,
            headers=self.auth_headers_funcionario,
        )

        # Verifica que a atualização foi proibida
        self.assertEqual(response.status_code, 403)

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

    def test_atualiza_funcionario_id_inexistente_sem_autorizacao(self):
        self.cria_funcionario()
        self.login_funcionario()

        payload = {
            "nome": "Fulaninho Games",
            "senha": "Jorginho123",
            "email": "novoemail@email.com",
            "tipo": "funcionario",
        }
        response = client.put(
            "/funcionario/99999/",
            json=payload,
            headers=self.auth_headers_funcionario,
        )

        self.assertEqual(response.status_code, 403)

    def test_atualiza_funcionario_sem_nome(self):
        self.cria_funcionario()
        funcionario = self.busca_funcionario_por_cpf("79920205451").json()["items"][0]

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
            "nome": funcionario["nome"],  # mantém o nome original
            "email": "novoemail@email.com",
            "tipo": "funcionario",
            "data_entrada": "2025-08-22",
        }

        self.assertEqual(response.status_code, 200)
        for campo, valor in payload_esperado.items():
            self.assertEqual(response.json()[campo], valor)

    def test_atualiza_funcionario_sem_nome_sem_autorizacao(self):
        self.cria_funcionario()
        self.login_funcionario()

        funcionario_data = {
            "cpf": "89159073454",
            "nome": "John Tres",
            "senha": "John123!",
            "email": "john@tres.com",
            "tipo": "funcionario",
            "data_entrada": "2025-08-04",
        }
        self.cria_funcionario(funcionario_data)

        funcionario = self.busca_funcionario_por_cpf("89159073454").json()["items"][0]
        payload = {
            "senha": "Jorginho123",
            "email": "novoemail@email.com",
            "tipo": "funcionario",
        }

        response = client.put(
            f"/funcionario/{funcionario['id']}/",
            json=payload,
            headers=self.auth_headers_funcionario,
        )

        self.assertEqual(response.status_code, 403)

    def test_atualiza_funcionario_sem_senha(self):
        self.cria_funcionario()
        funcionario = self.busca_funcionario_por_cpf("79920205451").json()["items"][0]

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
            "data_entrada": "2025-08-22",
        }

        self.assertEqual(response.status_code, 200)
        for campo, valor in payload_esperado.items():
            self.assertEqual(response.json()[campo], valor)

    def test_atualiza_funcionario_sem_senha_sem_autorizacao(self):
        self.cria_funcionario()
        self.login_funcionario()

        funcionario_data = {
            "cpf": "89159073454",
            "nome": "John Tres",
            "senha": "John123!",
            "email": "john@tres.com",
            "tipo": "funcionario",
            "data_entrada": "2025-08-04",
        }
        self.cria_funcionario(funcionario_data)

        funcionario = self.busca_funcionario_por_cpf("89159073454").json()["items"][0]
        payload = {
            "nome": "Fulaninho Games",
            "email": "novoemail@email.com",
            "tipo": "funcionario",
        }

        response = client.put(
            f"/funcionario/{funcionario['id']}/",
            json=payload,
            headers=self.auth_headers_funcionario,
        )

        self.assertEqual(response.status_code, 403)

    def test_atualiza_funcionario_sem_email(self):
        self.cria_funcionario()
        funcionario = self.busca_funcionario_por_cpf("79920205451").json()["items"][0]

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
            "data_entrada": "2025-08-22",
        }

        self.assertEqual(response.status_code, 200)
        for campo, valor in payload_esperado.items():
            self.assertEqual(response.json()[campo], valor)

    def test_atualiza_funcionario_sem_email_sem_autorizacao(self):
        self.cria_funcionario()
        self.login_funcionario()

        funcionario_data = {
            "cpf": "89159073454",
            "nome": "John Tres",
            "senha": "John123!",
            "email": "john@tres.com",
            "tipo": "funcionario",
            "data_entrada": "2025-08-04",
        }
        self.cria_funcionario(funcionario_data)

        funcionario = self.busca_funcionario_por_cpf("89159073454").json()["items"][0]

        payload = {
            "nome": "Fulaninho Games",
            "senha": "Jorginho123",
            "tipo": "funcionario",
        }

        response = client.put(
            f"/funcionario/{funcionario['id']}/",
            json=payload,
            headers=self.auth_headers_funcionario,
        )

        self.assertEqual(response.status_code, 403)

    def test_atualiza_funcionario_sem_tipo(self):
        self.cria_funcionario()
        funcionario = self.busca_funcionario_por_cpf("79920205451").json()["items"][0]
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
            "data_entrada": "2025-08-22",
        }

        self.assertEqual(response.status_code, 200)
        for campo, valor in payload_esperado.items():
            self.assertEqual(response.json()[campo], valor)

    def test_atualiza_funcionario_sem_tipo_sem_autorizacao(self):
        self.cria_funcionario()
        self.login_funcionario()

        funcionario_data = {
            "cpf": "89159073454",
            "nome": "John Tres",
            "senha": "John123!",
            "email": "john@tres.com",
            "tipo": "funcionario",
            "data_entrada": "2025-08-04",
        }
        self.cria_funcionario(funcionario_data)

        funcionario = self.busca_funcionario_por_cpf("89159073454").json()["items"][0]
        payload = {
            "nome": "Fulaninho Games",
            "senha": "Jorginho123",
            "email": "novoemail@email.com",
        }

        response = client.put(
            f"/funcionario/{funcionario['id']}/",
            json=payload,
            headers=self.auth_headers_funcionario,
        )

        self.assertEqual(response.status_code, 403)

    def test_atualiza_funcionario_payload_vazio(self):
        # Cria um funcionário
        self.cria_funcionario()

        # Busca o funcionário recém-criado
        funcionario = self.busca_funcionario_por_cpf("79920205451").json()["items"][0]

        # Payload vazio (não atualiza nenhum campo)
        payload = {}

        # Atualiza o funcionário com payload vazio
        response = client.put(
            f"/funcionario/{funcionario['id']}/",
            json=payload,
            headers=self.auth_headers,
        )

        # Espera-se que os dados permaneçam iguais
        payload_esperado = {
            "cpf": funcionario["cpf"],
            "nome": funcionario["nome"],
            "email": funcionario["email"],
            "tipo": funcionario["tipo"],
            "data_entrada": "2025-08-22",
        }

        # Verifica status de sucesso
        self.assertEqual(response.status_code, 200)

        # Verifica que todos os campos esperados estão corretos
        for campo, valor in payload_esperado.items():
            self.assertEqual(response.json()[campo], valor)

    def test_atualiza_funcionario_payload_vazio_sem_autorizacao(self):
        # Cria um funcionário e faz login com outro usuário
        self.cria_funcionario()
        self.login_funcionario()

        # Cria um segundo funcionário que será o alvo da atualização
        funcionario_data = {
            "cpf": "89159073454",
            "nome": "John Tres",
            "senha": "John123!",
            "email": "john@tres.com",
            "tipo": "funcionario",
            "data_entrada": "2025-08-04",
        }
        self.cria_funcionario(funcionario_data)

        # Busca o funcionário recém-criado
        funcionario = self.busca_funcionario_por_cpf("89159073454").json()["items"][0]

        # Payload vazio
        payload = {}

        # Tenta atualizar usando credenciais sem permissão
        response = client.put(
            f"/funcionario/{funcionario['id']}/",
            json=payload,
            headers=self.auth_headers_funcionario,
        )

        # Verifica que a atualização foi proibida
        self.assertEqual(response.status_code, 403)

    def test_atualiza_funcionario_email_invalido(self):
        # Cria funcionário padrão
        self.cria_funcionario()

        # Busca o funcionário criado
        funcionario = self.busca_funcionario_por_cpf("79920205451").json()["items"][0]

        # Payload com email inválido
        payload = {"email": "emailinvalido.com"}

        # Tenta atualizar o funcionário com email inválido
        response = client.put(
            f"/funcionario/{funcionario['id']}/",
            json=payload,
            headers=self.auth_headers,
        )

        # Verifica se o status code é 422 (Unprocessable Entity)
        self.assertEqual(response.status_code, 422)

        # Verifica se o erro retornado é referente a email inválido
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

    def test_atualiza_funcionario_email_invalido_sem_autorizacao(self):
        # Cria funcionário padrão
        self.cria_funcionario()
        self.login_funcionario()

        # Cria funcionário com CPF específico para teste
        funcionario_email_invalido = {
            "cpf": "89159073454",
            "nome": "John Tres",
            "senha": "John123!",
            "email": "john@tres.com",
            "tipo": "funcionario",
            "data_entrada": "2025-08-04",
        }
        self.cria_funcionario(funcionario_email_invalido)

        # Busca o funcionário criado
        funcionario = self.busca_funcionario_por_cpf("89159073454").json()["items"][0]

        # Tenta atualizar com email inválido sem autorização adequada
        payload = {"email": "emailinvalido.com"}
        response = client.put(
            f"/funcionario/{funcionario['id']}/",
            json=payload,
            headers=self.auth_headers_funcionario,
        )

        # Espera-se que a atualização seja proibida (403)
        self.assertEqual(response.status_code, 403)

    def test_atualiza_funcionario_tipo_invalido(self):
        self.cria_funcionario()
        funcionario = self.busca_funcionario_por_cpf("79920205451").json()["items"][0]
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

    def test_atualiza_funcionario_tipo_invalido_sem_autorizacao(self):
        self.cria_funcionario()
        self.login_funcionario()

        funcionario_tipo_invalido = {
            "cpf": "89159073454",
            "nome": "John Tres",
            "senha": "John123!",
            "email": "john@tres.com",
            "tipo": "funcionario",
            "data_entrada": "2025-08-04",
        }
        self.cria_funcionario(funcionario_tipo_invalido)

        funcionario = self.busca_funcionario_por_cpf("89159073454").json()["items"][0]
        payload = {"tipo": "cliente"}

        response = client.put(
            f"/funcionario/{funcionario['id']}/",
            json=payload,
            headers=self.auth_headers_funcionario,
        )

        self.assertEqual(response.status_code, 403)

    def test_busca_funcionarios_sem_funcionarios(self):
        # Deixa a tabela de funcionarios vazia
        self.tearDown()
        response = client.get("/funcionario/", headers=self.auth_headers)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_busca_funcionarios_sem_funcionarios_sem_autorizacao(self):
        # Deixa a tabela de funcionarios vazia
        self.tearDown()
        response = client.get("/funcionario/", headers=self.auth_headers_invalido)

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_funcionarios_sem_parametros(self):
        # Cria funcionários padrão
        self.cria_funcionario()
        self.cria_funcionario(
            {
                "cpf": "19896507406",
                "nome": "Outro Funcionario",
                "senha": "Senha123!",
                "email": "outro@funcionario.com",
                "tipo": "funcionario",
                "data_entrada": "2025-08-04",
            }
        )

        # Faz a requisição GET sem parâmetros
        response = client.get("/funcionario/", headers=self.auth_headers)

        # Verifica se o status code é 200
        self.assertEqual(response.status_code, 200)

        # Obtém os funcionários esperados
        funcionario1 = self.busca_funcionario_por_cpf("79920205451").json()["items"][0]

        # Obtém a lista de funcionários retornada pelo endpoint
        funcionarios_retornados = response.json().get("items", [])

        # Verifica se ambos os funcionários estão na resposta
        self.assertIn(funcionario1, funcionarios_retornados)

    def test_funcionario_busca_funcionarios_sem_parametros(self):
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get("/funcionario/", headers=self.auth_headers_funcionario)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        nomes_retornados = [f["nome"] for f in data["items"]]

        self.assertIn(data["items"][0]["nome"], nomes_retornados)

        # (Opcional) Validar os metadados de paginação
        self.assertGreaterEqual(data["total_in_page"], 1)
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 10)
        self.assertGreaterEqual(data["total_pages"], 1)

    def test_busca_funcionarios_sem_parametros_sem_autorizacao(self):
        self.cria_funcionario()
        response = client.get("/funcionario/", headers=self.auth_headers_invalido)

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_funcionarios_por_id(self):
        self.cria_funcionario()
        funcionario = self.busca_funcionario_por_cpf("79920205451").json()["items"][0]
        response = client.get(
            f"/funcionario/?id={funcionario['id']}", headers=self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_funcionario_por_cpf("79920205451").json()["items"],
            response.json()["items"],
        )

    def test_funcionario_busca_funcionarios_por_id(self):
        self.cria_funcionario()
        self.login_funcionario()
        funcionario = self.busca_funcionario_por_cpf("79920205451").json()["items"][0]

        response = client.get(
            f"/funcionario/?id={funcionario['id']}",
            headers=self.auth_headers_funcionario,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_funcionario_por_cpf("79920205451").json()["items"],
            response.json()["items"],
        )

    def test_busca_funcionarios_por_id_sem_autorizacao(self):
        self.cria_funcionario()
        funcionario = self.busca_funcionario_por_cpf("79920205451").json()["items"][0]

        response = client.get(
            f"/funcionario/?id={funcionario['id']}",
            headers=self.auth_headers_invalido,
        )

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_funcionarios_por_id_inexistente(self):
        self.cria_funcionario()
        response = client.get("/funcionario/?id=9999", headers=self.auth_headers)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_funcionario_busca_funcionarios_por_id_inexistente(self):
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get(
            "/funcionario/?id=9999", headers=self.auth_headers_funcionario
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_busca_funcionarios_por_id_inexistente_sem_autorizacao(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/?id=9999", headers=self.auth_headers_invalido
        )

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_funcionarios_por_cpf(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/?cpf=79920205451", headers=self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_funcionario_por_cpf("79920205451").json(), response.json()
        )

    def test_funcionario_busca_funcionarios_por_cpf(self):
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get(
            "/funcionario/?cpf=79920205451", headers=self.auth_headers_funcionario
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_funcionario_por_cpf("79920205451").json()["items"],
            response.json()["items"],
        )

    def test_busca_funcionarios_por_cpf_sem_autorizacao(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/?cpf=79920205451", headers=self.auth_headers_invalido
        )

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_funcionarios_por_cpf_inexistente(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/?cpf=12345678910", headers=self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_funcionario_busca_funcionarios_por_cpf_inexistente(self):
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get(
            "/funcionario/?cpf=12345678910", headers=self.auth_headers_funcionario
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_busca_funcionarios_por_cpf_inexistente_sem_autorizacao(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/?cpf=12345678910", headers=self.auth_headers_invalido
        )

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_funcionarios_por_nome(self):
        self.funcionario_padrao["nome"] = "Joao"
        self.cria_funcionario()
        response = client.get("/funcionario/?nome=Joao", headers=self.auth_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_funcionario_por_cpf("79920205451").json(), response.json()
        )

    def test_funcionario_busca_funcionarios_por_nome(self):
        self.funcionario_padrao["nome"] = "Joao"
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get(
            "/funcionario/?nome=Joao", headers=self.auth_headers_funcionario
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_funcionario_por_cpf("79920205451").json(), response.json()
        )

    def test_busca_funcionarios_por_nome_sem_autorizacao(self):
        self.funcionario_padrao["nome"] = "Joao"
        self.cria_funcionario()
        response = client.get(
            "/funcionario/?nome=Joao", headers=self.auth_headers_invalido
        )

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_funcionarios_por_nome_inexistente(self):
        self.funcionario_padrao["nome"] = "Jose"
        self.cria_funcionario()
        response = client.get("/funcionario/?nome=Joao", headers=self.auth_headers)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_funcionario_busca_funcionarios_por_nome_inexistente(self):
        self.funcionario_padrao["nome"] = "Jose"
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get(
            "/funcionario/?nome=Joao", headers=self.auth_headers_funcionario
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_busca_funcionarios_por_nome_inexistente_sem_autorizacao(self):
        self.funcionario_padrao["nome"] = "Jose"
        self.cria_funcionario()
        response = client.get(
            "/funcionario/?nome=Joao", headers=self.auth_headers_invalido
        )

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_funcionarios_por_email(self):
        self.funcionario_padrao["nome"] = "Joao"
        self.cria_funcionario()
        response = client.get("/funcionario/?nome=Joao", headers=self.auth_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_funcionario_por_cpf("79920205451").json(), response.json()
        )

    def test_funcionario_busca_funcionarios_por_email(self):
        self.funcionario_padrao["nome"] = "Joao"
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get(
            "/funcionario/?nome=Joao", headers=self.auth_headers_funcionario
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_funcionario_por_cpf("79920205451").json(), response.json()
        )

    def test_busca_funcionarios_por_email_sem_autorizacao(self):
        self.funcionario_padrao["nome"] = "Joao"
        self.cria_funcionario()
        response = client.get(
            "/funcionario/?nome=Joao", headers=self.auth_headers_invalido
        )

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_funcionarios_por_email_inexistente(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/?email=john@tres.com", headers=self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_funcionario_busca_funcionarios_por_email_inexistente(self):
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get(
            "/funcionario/?email=john@tres.com", headers=self.auth_headers_funcionario
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_busca_funcionarios_por_email_inexistente_sem_autorizacao(self):
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get(
            "/funcionario/?email=john@tres.com", headers=self.auth_headers_invalido
        )

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_funcionarios_por_data_entrada(self):
        # Cria funcionários
        funcionario_data = {
            "cpf": "89159073454",
            "nome": "John Tres",
            "senha": "John123!",
            "email": "john@tres.com",
            "tipo": "funcionario",
            "data_entrada": "2025-08-22",
        }
        self.cria_funcionario(funcionario_data)

        # Faz a requisição GET filtrando pela data de entrada
        response = client.get(
            "/funcionario/?data_entrada=2025-08-22", headers=self.auth_headers
        )

        # Verifica se o status code é 200
        self.assertEqual(response.status_code, 200)

        # Obtém os funcionários filtrados pelo CPF
        funcionario_filtrado = self.busca_funcionario_por_cpf("89159073454").json()[
            "items"
        ][0]

        # Verifica se o funcionário correto está na resposta
        funcionarios_retornados = response.json().get("items", [])
        self.assertIn(funcionario_filtrado, funcionarios_retornados)

    def test_funcionario_busca_funcionarios_por_data_entrada(self):
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get(
            "/funcionario/?data_entrada=2025-08-22",
            headers=self.auth_headers_funcionario,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            self.busca_funcionario_por_cpf("79920205451").json()["items"][0],
            response.json()["items"],
        )

    def test_busca_funcionarios_por_data_entrada_sem_autorizacao(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/?data_entrada=2025-08-04", headers=self.auth_headers_invalido
        )

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_funcionarios_por_data_entrada_inexistente(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/?data_entrada=2005-02-13", headers=self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_funcionario_busca_funcionarios_por_data_entrada_inexistente(self):
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get(
            "/funcionario/?data_entrada=2005-02-13",
            headers=self.auth_headers_funcionario,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_busca_funcionarios_por_data_entrada_inexistente_sem_autorizacao(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/?data_entrada=2005-02-13", headers=self.auth_headers_invalido
        )

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_funcionarios_por_data_saida(self):
        # Cria o funcionário
        self.cria_funcionario()

        # Define a data de saída e desativa o funcionário
        data_saida = date.today()
        client.post(
            f"/funcionario/79920205451/desativar?data_saida={data_saida}",
            headers=self.auth_headers,
        )

        # Faz a requisição GET filtrando pela data de saída
        response = client.get(
            f"/funcionario/?data_saida={data_saida}", headers=self.auth_headers
        )

        # Verifica se o status code é 200
        self.assertEqual(response.status_code, 200)

        # Obtém o funcionário desativado
        funcionario_desativado = self.busca_funcionario_por_cpf("79920205451").json()[
            "items"
        ][0]

        # Obtém a lista de funcionários retornada pelo endpoint
        funcionarios_retornados = response.json().get("items", [])

        # Verifica se o funcionário desativado está na resposta
        self.assertIn(funcionario_desativado, funcionarios_retornados)

        # Verifica se o email do funcionário desativado foi removido
        self.assertIsNone(funcionario_desativado.get("email"))

    def test_funcionario_busca_funcionarios_por_data_saida(self):
        self.cria_funcionario()
        data_saida = date.today()
        client.post(
            f"/funcionario/79920205451/desativar?data_saida={data_saida}",
            headers=self.auth_headers,
        )

        self.login_funcionario()
        response = client.get(
            f"/funcionario/?data_saida={data_saida}",
            headers=self.auth_headers_funcionario,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_funcionario_por_cpf("79920205451").json()["items"],
            response.json()["items"],
        )
        self.assertIsNone(
            self.busca_funcionario_por_cpf("79920205451").json()["items"][0]["email"]
        )

    def test_busca_funcionarios_por_data_saida_sem_autorizacao(self):
        self.cria_funcionario()
        data_saida = date.today()
        client.post(
            f"/funcionario/79920205451/desativar?data_saida={data_saida}",
            headers=self.auth_headers,
        )

        response = client.get(
            f"/funcionario/?data_saida={data_saida}", headers=self.auth_headers_invalido
        )

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_funcionarios_por_data_saida_inexistente(self):
        self.cria_funcionario()
        data_saida = date.today()
        response = client.get(
            f"/funcionario/?data_saida={data_saida}", headers=self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_funcionario_busca_funcionarios_por_data_saida_inexistente(self):
        self.cria_funcionario()
        self.login_funcionario()
        data_saida = date.today()
        response = client.get(
            f"/funcionario/?data_saida={data_saida}",
            headers=self.auth_headers_funcionario,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_busca_funcionarios_por_data_saida_inexistente_sem_autorizacao(self):
        self.cria_funcionario()
        data_saida = date.today()
        response = client.get(
            f"/funcionario/?data_saida={data_saida}", headers=self.auth_headers_invalido
        )

        self.assertEqual(response.status_code, 401)

    def test_busca_admins_sem_funcionarios(self):
        # Deixa a tabela de funcionarios vazia
        self.tearDown()
        response = client.get("/funcionario/admin/", headers=self.auth_headers)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_busca_admins_sem_funcionarios_sem_autorizacao(self):
        # Deixa a tabela de funcionarios vazia
        self.tearDown()
        response = client.get("/funcionario/admin/", headers=self.auth_headers_invalido)

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_admins_sem_parametros(self):
        # Faz a requisição GET sem parâmetros
        response = client.get("/funcionario/admin/", headers=self.auth_headers)

        # Verifica se o status code é 200
        self.assertEqual(response.status_code, 200)

        # Obtém o funcionário esperado
        funcionario = self.busca_admin_por_cpf("19896507406").json()["items"][0]

        # Obtém a lista de funcionários retornada pelo endpoint
        funcionarios_retornados = response.json().get("items", [])

        # Verifica se o funcionário está na resposta
        self.assertIn(funcionario, funcionarios_retornados)

    def test_funcionario_busca_admins_sem_parametros(self):
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get(
            "/funcionario/admin/", headers=self.auth_headers_funcionario
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        nomes_retornados = [f["nome"] for f in data["items"]]

        self.assertIn(data["items"][0]["nome"], nomes_retornados)

        # (Opcional) Validar os metadados de paginação
        self.assertGreaterEqual(data["total_in_page"], 1)
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 10)
        self.assertGreaterEqual(data["total_pages"], 1)

    def test_busca_admins_sem_parametros_sem_autorizacao(self):
        self.cria_funcionario()
        response = client.get("/funcionario/admin/", headers=self.auth_headers_invalido)

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_admins_por_id(self):
        self.cria_funcionario()
        funcionario = self.busca_admin_por_cpf("19896507406").json()["items"][0]
        response = client.get(
            f"/funcionario/admin/?id={funcionario['id']}", headers=self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_admin_por_cpf("19896507406").json()["items"],
            response.json()["items"],
        )

    def test_funcionario_busca_admins_por_id(self):
        self.cria_funcionario()
        self.login_funcionario()
        funcionario = self.busca_admin_por_cpf("19896507406").json()["items"][0]

        response = client.get(
            f"/funcionario/admin/?id={funcionario['id']}",
            headers=self.auth_headers_funcionario,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_admin_por_cpf("19896507406").json()["items"],
            response.json()["items"],
        )

    def test_busca_admins_por_id_sem_autorizacao(self):
        self.cria_funcionario()
        funcionario = self.busca_admin_por_cpf("19896507406").json()["items"][0]

        response = client.get(
            f"/funcionario/admin/?id={funcionario['id']}",
            headers=self.auth_headers_invalido,
        )

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_admins_por_id_inexistente(self):
        self.cria_funcionario()
        response = client.get("/funcionario/admin/?id=9999", headers=self.auth_headers)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_funcionario_busca_admins_por_id_inexistente(self):
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get(
            "/funcionario/admin/?id=9999", headers=self.auth_headers_funcionario
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_busca_admins_por_id_inexistente_sem_autorizacao(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/admin/?id=9999", headers=self.auth_headers_invalido
        )

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_admins_por_cpf(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/admin/?cpf=19896507406", headers=self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_admin_por_cpf("19896507406").json(), response.json()
        )

    def test_funcionario_busca_admins_por_cpf(self):
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get(
            "/funcionario/admin/?cpf=19896507406", headers=self.auth_headers_funcionario
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_admin_por_cpf("19896507406").json()["items"],
            response.json()["items"],
        )

    def test_busca_admins_por_cpf_sem_autorizacao(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/admin/?cpf=19896507406", headers=self.auth_headers_invalido
        )

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_admins_por_cpf_inexistente(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/admin/?cpf=12345678910", headers=self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_funcionario_busca_admins_por_cpf_inexistente(self):
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get(
            "/funcionario/admin/?cpf=12345678910", headers=self.auth_headers_funcionario
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_busca_admins_por_cpf_inexistente_sem_autorizacao(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/admin/?cpf=12345678910", headers=self.auth_headers_invalido
        )

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_admins_por_nome(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/admin/?nome=John Doe", headers=self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_admin_por_cpf("19896507406").json(), response.json()
        )

    def test_funcionario_busca_admins_por_nome(self):
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get(
            "/funcionario/admin/?nome=John Doe", headers=self.auth_headers_funcionario
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_admin_por_cpf("19896507406").json(), response.json()
        )

    def test_busca_admins_por_nome_sem_autorizacao(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/admin/?nome=John Doe", headers=self.auth_headers_invalido
        )

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_admins_por_nome_inexistente(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/admin/?nome=Joao", headers=self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_funcionario_busca_admins_por_nome_inexistente(self):
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get(
            "/funcionario/admin/?nome=Joao", headers=self.auth_headers_funcionario
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_busca_admins_por_nome_inexistente_sem_autorizacao(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/admin/?nome=Joao", headers=self.auth_headers_invalido
        )

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_admins_por_email(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/admin/?email=john@doe.com", headers=self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_admin_por_cpf("19896507406").json(), response.json()
        )

    def test_funcionario_busca_admins_por_email(self):
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get(
            "/funcionario/admin/?email=john@doe.com",
            headers=self.auth_headers_funcionario,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.busca_admin_por_cpf("19896507406").json(), response.json()
        )

    def test_busca_admins_por_email_sem_autorizacao(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/admin/?email=john@doe.com", headers=self.auth_headers_invalido
        )

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_admins_por_email_inexistente(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/admin/?email=john@tres.com", headers=self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_funcionario_busca_admins_por_email_inexistente(self):
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get(
            "/funcionario/admin/?email=john@tres.com",
            headers=self.auth_headers_funcionario,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_busca_admins_por_email_inexistente_sem_autorizacao(self):
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get(
            "/funcionario/admin/?email=john@tres.com",
            headers=self.auth_headers_invalido,
        )

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_admins_por_data_entrada(self):
        # Faz a requisição GET filtrando pela data de entrada
        response = client.get(
            "/funcionario/admin/?data_entrada=2025-08-04", headers=self.auth_headers
        )

        # Verifica se o status code é 200
        self.assertEqual(response.status_code, 200)

        # Obtém o funcionário filtrado pela data de entrada
        funcionario_filtrado = self.busca_admin_por_cpf("19896507406").json()["items"][
            0
        ]

        # Verifica se o funcionário correto está na resposta
        funcionarios_retornados = response.json().get("items", [])
        self.assertIn(funcionario_filtrado, funcionarios_retornados)

    def test_funcionario_busca_admins_por_data_entrada(self):
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get(
            "/funcionario/admin/?data_entrada=2025-08-04",
            headers=self.auth_headers_funcionario,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            self.busca_admin_por_cpf("19896507406").json()["items"][0],
            response.json()["items"],
        )

    def test_busca_admins_por_data_entrada_sem_autorizacao(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/admin/?data_entrada=2025-08-04",
            headers=self.auth_headers_invalido,
        )

        self.assertEqual(response.status_code, 401)

    def test_admin_busca_admins_por_data_entrada_inexistente(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/admin/?data_entrada=2005-02-13", headers=self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_funcionario_busca_admin_por_data_entrada_inexistente(self):
        self.cria_funcionario()
        self.login_funcionario()
        response = client.get(
            "/funcionario/admin/?data_entrada=2005-02-13",
            headers=self.auth_headers_funcionario,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])
        self.assertEqual(0, data["total_pages"])

    def test_busca_admins_por_data_entrada_inexistente_sem_autorizacao(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/admin/?data_entrada=2005-02-13",
            headers=self.auth_headers_invalido,
        )

        self.assertEqual(response.status_code, 401)

    def test_deleta_funcionario_com_sucesso(self):
        self.cria_funcionario()
        response = client.delete(
            "/funcionario/?cpf=79920205451", headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Funcionário deletado com sucesso", response.text)

    def test_deleta_funcionario_com_sucesso_sem_autorizacao(self):
        self.cria_funcionario()

        funcionario_deletado = {
            "cpf": "89159073454",
            "nome": "John Tres",
            "senha": "John123!",
            "email": "john@tres.com",
            "tipo": "funcionario",
            "data_entrada": "2025-08-04",
        }
        self.cria_funcionario(funcionario_deletado)

        self.login_funcionario()
        response = client.delete(
            "/funcionario/?cpf=89159073454", headers=self.auth_headers_funcionario
        )
        self.assertEqual(response.status_code, 403)

    def test_deleta_funcionario_cpf_inexistente(self):
        self.cria_funcionario()
        response = client.delete(
            "/funcionario/?cpf=80799286575", headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("Funcionário não encontrado", response.text)

    def test_deleta_funcionario_cpf_inexistente_sem_autorizacao(self):
        self.cria_funcionario()
        self.login_funcionario()
        response = client.delete(
            "/funcionario/?cpf=80799286575", headers=self.auth_headers_funcionario
        )
        self.assertEqual(response.status_code, 403)

    def test_desativa_funcionario_com_sucesso(self):
        self.cria_funcionario()
        data_saida = date.today()
        response = client.post(
            f"/funcionario/79920205451/desativar?data_saida={data_saida}",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Funcionário desativado com sucesso", response.text)

    def test_desativa_funcionario_sem_autorizacao(self):
        self.cria_funcionario()

        funcionario_desativado = {
            "cpf": "89159073454",
            "nome": "John Tres",
            "senha": "John123!",
            "email": "john@tres.com",
            "tipo": "funcionario",
            "data_entrada": "2025-08-04",
        }
        self.cria_funcionario(funcionario_desativado)

        self.login_funcionario()
        data_saida = date.today()
        response = client.post(
            f"/funcionario/89159073454/desativar?data_saida={data_saida}",
            headers=self.auth_headers_funcionario,
        )
        self.assertEqual(response.status_code, 403)

    def test_desativa_funcionario_cpf_inexistente(self):
        self.cria_funcionario()
        data_saida = date.today()
        response = client.post(
            f"/funcionario/80799286575/desativar?data_saida={data_saida}",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("Funcionário não encontrado", response.text)

    def test_desativa_funcionario_cpf_inexistente_sem_autorizacao(self):
        self.cria_funcionario()
        self.login_funcionario()

        funcionario_desativado = {
            "cpf": "89159073454",
            "nome": "John Tres",
            "senha": "John123!",
            "email": "john@tres.com",
            "tipo": "funcionario",
            "data_entrada": "2025-08-04",
        }
        self.cria_funcionario(funcionario_desativado)

        data_saida = date.today()
        response = client.post(
            f"/funcionario/80799286575/desativar?data_saida={data_saida}",
            headers=self.auth_headers_funcionario,
        )
        self.assertEqual(response.status_code, 403)

    # ===== Testes para novas rotas de listagem paginada =====
    # /funcionario/listar/admin
    def test_listar_admins_sem_autorizacao(self):
        response = client.get(
            "/funcionario/listar/admin", headers=self.auth_headers_invalido
        )
        self.assertEqual(response.status_code, 401)

    def test_listar_admins_sem_parametros(self):
        response = client.get("/funcionario/listar/admin", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        admin = self.busca_admin_por_cpf("19896507406").json()["items"][0]
        itens = response.json().get("items", [])
        self.assertIn(admin, itens)
        data = response.json()
        self.assertEqual(1, data["page"])
        self.assertEqual(10, data["page_size"])

    def test_listar_admins_busca_por_nome(self):
        response = client.get(
            "/funcionario/listar/admin?busca=John%20Doe", headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        esperado = self.busca_admin_por_cpf("19896507406").json()["items"]
        self.assertEqual(esperado, response.json()["items"]) 

    def test_listar_admins_busca_por_email(self):
        response = client.get(
            "/funcionario/listar/admin?busca=john@doe.com", headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        esperado = self.busca_admin_por_cpf("19896507406").json()["items"]
        self.assertEqual(esperado, response.json()["items"]) 

    def test_listar_admins_busca_por_tipo(self):
        response = client.get(
            "/funcionario/listar/admin?busca=admin", headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        admin = self.busca_admin_por_cpf("19896507406").json()["items"][0]
        self.assertIn(admin, response.json().get("items", []))

    def test_listar_admins_busca_por_id(self):
        admin = self.busca_admin_por_cpf("19896507406").json()["items"][0]
        response = client.get(
            f"/funcionario/listar/admin?busca={admin['id']}", headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(admin, response.json().get("items", []))

    def test_listar_admins_busca_por_cpf(self):
        response = client.get(
            "/funcionario/listar/admin?busca=19896507406", headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        esperado = self.busca_admin_por_cpf("19896507406").json()["items"]
        self.assertEqual(esperado, response.json()["items"]) 

    def test_listar_admins_busca_por_data_iso(self):
        response = client.get(
            "/funcionario/listar/admin?busca=2025-08-04", headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        admin = self.busca_admin_por_cpf("19896507406").json()["items"][0]
        self.assertIn(admin, response.json().get("items", []))

    def test_listar_admins_busca_por_data_br(self):
        response = client.get(
            "/funcionario/listar/admin?busca=04/08/2025", headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        admin = self.busca_admin_por_cpf("19896507406").json()["items"][0]
        self.assertIn(admin, response.json().get("items", []))

    def test_listar_admins_busca_inexistente(self):
        response = client.get(
            "/funcionario/listar/admin?busca=nao_encontrara_aqui_123",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])

    def test_listar_admins_paginacao(self):
        response = client.get(
            "/funcionario/listar/admin?page=1&page_size=1",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(1, data["page"])
        self.assertEqual(1, data["page_size"])
        self.assertGreaterEqual(data["total_in_page"], 1)
        self.assertGreaterEqual(data["total_pages"], 1)

    # /funcionario/listar/funcionario/
    def test_listar_funcionarios_sem_autorizacao(self):
        response = client.get(
            "/funcionario/listar/funcionario/", headers=self.auth_headers_invalido
        )
        self.assertEqual(response.status_code, 401)

    def test_listar_funcionarios_sem_parametros(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/listar/funcionario/", headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        func = self.busca_funcionario_por_cpf("79920205451").json()["items"][0]
        itens = response.json().get("items", [])
        self.assertIn(func, itens)
        data = response.json()
        self.assertEqual(1, data["page"])
        self.assertEqual(10, data["page_size"])

    def test_listar_funcionarios_busca_por_nome(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/listar/funcionario/?busca=John%20Dois",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 200)
        esperado = self.busca_funcionario_por_cpf("79920205451").json()["items"]
        self.assertEqual(esperado, response.json()["items"]) 

    def test_listar_funcionarios_busca_por_email(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/listar/funcionario/?busca=john@dois.com",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 200)
        esperado = self.busca_funcionario_por_cpf("79920205451").json()["items"]
        self.assertEqual(esperado, response.json()["items"]) 

    def test_listar_funcionarios_busca_por_tipo(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/listar/funcionario/?busca=funcionario",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 200)
        func = self.busca_funcionario_por_cpf("79920205451").json()["items"][0]
        self.assertIn(func, response.json().get("items", []))

    def test_listar_funcionarios_busca_por_id(self):
        self.cria_funcionario()
        func = self.busca_funcionario_por_cpf("79920205451").json()["items"][0]
        response = client.get(
            f"/funcionario/listar/funcionario/?busca={func['id']}",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(func, response.json().get("items", []))

    def test_listar_funcionarios_busca_por_cpf(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/listar/funcionario/?busca=79920205451",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 200)
        esperado = self.busca_funcionario_por_cpf("79920205451").json()["items"]
        self.assertEqual(esperado, response.json()["items"]) 

    def test_listar_funcionarios_busca_por_data_iso(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/listar/funcionario/?busca=2025-08-22",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 200)
        func = self.busca_funcionario_por_cpf("79920205451").json()["items"][0]
        self.assertIn(func, response.json().get("items", []))

    def test_listar_funcionarios_busca_por_data_br(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/listar/funcionario/?busca=22/08/2025",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 200)
        func = self.busca_funcionario_por_cpf("79920205451").json()["items"][0]
        self.assertIn(func, response.json().get("items", []))

    def test_listar_funcionarios_busca_inexistente(self):
        self.cria_funcionario()
        response = client.get(
            "/funcionario/listar/funcionario/?busca=nao_encontrara_aqui_123",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([], data["items"])
        self.assertEqual(0, data["total_in_page"])

    def test_listar_funcionarios_paginacao(self):
        # cria dois funcionarios para paginar
        self.cria_funcionario()
        self.cria_funcionario(
            {
                "cpf": "89159073454",
                "nome": "John Tres",
                "senha": "John123!",
                "email": "john@tres.com",
                "tipo": "funcionario",
                "data_entrada": "2025-08-22",
            }
        )
        resp1 = client.get(
            "/funcionario/listar/funcionario/?page=1&page_size=1",
            headers=self.auth_headers,
        )
        resp2 = client.get(
            "/funcionario/listar/funcionario/?page=2&page_size=1",
            headers=self.auth_headers,
        )
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp2.status_code, 200)
        d1, d2 = resp1.json(), resp2.json()
        self.assertEqual(1, d1["page"])
        self.assertEqual(2, d2["page"])
        self.assertEqual(1, d1["page_size"])
        self.assertEqual(1, d2["page_size"])
        self.assertEqual(1, d1["total_in_page"])
        self.assertEqual(1, d2["total_in_page"])
        cpfs = {f["cpf"] for f in d1["items"] + d2["items"]}
        self.assertIn("79920205451", cpfs)
        self.assertIn("89159073454", cpfs)
