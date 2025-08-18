import io
import unittest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.models import Cliente
from app.models.db_setup import engine
from app.core.seguranca import hash_cpf
import polars as pl

client = TestClient(app)


class ClienteTestCase(unittest.TestCase):
    def setUp(self):
        self.client = client
        self.db: Session = Session(bind=engine)
        # Limpa clientes com CPFs usados nos testes antes de cada teste
        cpfs_testados = [
            "12345678901",
            "39410861977",
            "1111111111",
            "222222222222",
            "33333abc33a",
        ]
        for cpf in cpfs_testados:
            cliente = self.db.query(Cliente).filter_by(cpf_hash=hash_cpf(cpf)).first()
            if cliente:
                self.db.delete(cliente)
        self.db.commit()

    def tearDown(self):
        # Limpa clientes após cada teste para garantir isolamento
        cpfs_testados = [
            "39410861977",
            "88451210031",
            "36452746006",
            "222222222222",
            "33333abc33a",
        ]
        for cpf in cpfs_testados:
            cliente = self.db.query(Cliente).filter_by(cpf_hash=hash_cpf(cpf)).first()
            if cliente:
                self.db.delete(cliente)
        self.db.commit()
        self.db.close()

    def test_cria_cliente(self):
        payload = {
            "cpf": "39410861977",
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
            "cpf": "39410861977",
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
            "cpf": "39410861977",
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
            "cpf": "39410861977",
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
        self.assertEqual(response.status_code, 400)

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
        self.assertEqual(response.status_code, 400)

    def test_remove_cliente_inexistente(self):
        response = self.client.delete("/cliente/39410861977")
        self.assertEqual(response.status_code, 404)

    def test_edita_cliente_matricula_invalida(self):
        payload = {
            "cpf": "39410861977",
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
        self.assertEqual(response.status_code, 422)

    def test_edita_cliente_tipo_invalido(self):
        payload = {
            "cpf": "39410861977",
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
        self.assertEqual(response.status_code, 422)

    def test_edita_cliente_sem_payload(self):
        payload = {
            "cpf": "39410861977",
            "nome": "Sem Payload",
            "matricula": "20240205",
            "tipo": "aluno",
            "graduando": True,
            "pos_graduando": False,
            "bolsista": True,
        }
        self.client.post("/cliente/", json=payload)
        response = self.client.put(f"/cliente/{payload['cpf']}", json={})
        self.assertEqual(response.status_code, 200)

    def test_rota_inexistente_get(self):
        response = self.client.get("/clientes/")
        self.assertEqual(response.status_code, 404)

    def test_rota_inexistente_post(self):
        response = self.client.post("/cliente/inexistente", json={})
        self.assertEqual(response.status_code, 405)

    def test_metodo_nao_permitido(self):
        response = self.client.post("/cliente/12345678901")
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
        self.client.post("/cliente/", json=payload)

        # tenta criar novamente com o mesmo CPF
        payload2 = payload.copy()
        payload2["nome"] = "Cliente Duplicado"
        response2 = self.client.post("/cliente/", json=payload2)

        # deve retornar erro de duplicidade: 400 (violação de chave) ou 422 (validação)
        self.assertEqual(response2.status_code, 400)

    def generate_csv_bytes(self, headers: list[str], rows: list[dict]) -> bytes:
        """Gera um CSV em bytes a partir de headers e linhas."""
        tabela = pl.DataFrame(rows)[headers]
        buf = io.BytesIO()
        tabela.write_csv(buf)
        return buf.getvalue()

    def test_upload_csv_sucesso(self):
        # CSV válido com uma linha
        headers = [
            "cpf",
            "nome",
            "matricula",
            "tipo",
            "graduando",
            "pos_graduando",
            "bolsista",
        ]
        rows = [
            {
                "cpf": "55566677788",
                "nome": "Cliente A",
                "matricula": "20240210",
                "tipo": "aluno",
                "graduando": True,
                "pos_graduando": False,
                "bolsista": False,
            },
        ]
        csv_bytes = self.generate_csv_bytes(headers, rows)

        response = self.client.post(
            "/cliente/upload-csv/",
            files={"arquivo": ("clientes.csv", csv_bytes, "text/csv")},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "1 cliente(s) cadastrado(s) com sucesso.")

        # Verifica no banco
        cliente = self.db.query(Cliente).filter_by(cpf_hash=hash_cpf("55566677788")).first()
        assert cliente is not None
        self.assertEqual(cliente.nome, "Cliente A")

        # **Limpeza**: deleta o cliente recém-criado para não interferir em próximos testes
        self.db.delete(cliente)
        self.db.commit()

    def test_upload_csv_extensao_invalida(self):
        csv_bytes = b"qualquer,conteudo\n"
        response = self.client.post(
            "/cliente/upload-csv/",
            files={"arquivo": ("clientes.txt", csv_bytes, "text/plain")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("deveria ser CSV", response.json()["detail"])

    def test_upload_csv_colunas_faltando(self):
        # Cabeçalho errado, faltam colunas obrigatórias
        headers = ["cpf", "nome", "matricula"]
        rows = [{"cpf": "55555555555", "nome": "Nome", "matricula": "20240211"}]
        csv_bytes = self.generate_csv_bytes(headers, rows)

        response = self.client.post(
            "/cliente/upload-csv/",
            files={"arquivo": ("clientes.csv", csv_bytes, "text/csv")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("não contém as colunas necessárias", response.json()["detail"])

    def test_filtrar_por_nome(self):
        clientes = [
            {
                "cpf": "39410861977",
                "nome": "Alice",
                "matricula": "MAT001",
                "tipo": "aluno",
                "graduando": True,
                "pos_graduando": False,
                "bolsista": True,
            },
            {
                "cpf": "88451210031",
                "nome": "Bob",
                "matricula": "MAT002",
                "tipo": "tecnico",
                "graduando": False,
                "pos_graduando": False,
                "bolsista": False,
            },
            {
                "cpf": "36452746006",
                "nome": "Alicia",
                "matricula": "MAT003",
                "tipo": "professor",
                "graduando": False,
                "pos_graduando": True,
                "bolsista": True,
            },
        ]
        for c in clientes:
            self.client.post("/cliente/", json=c)
        response = self.client.get("/cliente/?nome=Ali")
        self.assertEqual(response.status_code, 200)
        nomes = [c["nome"] for c in response.json()]
        self.assertIn("Alice", nomes)
        self.assertIn("Alicia", nomes)
        self.assertNotIn("Bob", nomes)

    def test_filtrar_por_tipo(self):
        self.client.post(
            "/cliente/",
            json={
                "cpf": "88451210031",
                "nome": "Bob",
                "matricula": "MAT002",
                "tipo": "tecnico",
                "graduando": False,
                "pos_graduando": False,
                "bolsista": False,
            },
        )
        response = self.client.get("/cliente/?tipo=tecnico")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["nome"], "Bob")

    def test_filtrar_por_matricula(self):
        self.client.post(
            "/cliente/",
            json={
                "cpf": "39410861977",
                "nome": "Alicia",
                "matricula": "MAT003",
                "tipo": "professor",
                "graduando": False,
                "pos_graduando": True,
                "bolsista": True,
            },
        )
        response = self.client.get("/cliente/?matricula=MAT003")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["nome"], "Alicia")

    def test_filtrar_combinado(self):
        self.client.post(
            "/cliente/",
            json={
                "cpf": "39410861977",
                "nome": "Alice",
                "matricula": "MAT001",
                "tipo": "aluno",
                "graduando": True,
                "pos_graduando": False,
                "bolsista": True,
            },
        )
        response = self.client.get("/cliente/?nome=Ali&tipo=aluno")
        self.assertEqual(response.status_code, 200)
        resultados = response.json()
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0]["nome"], "Alice")

    def test_filtrar_sem_resultado(self):
        response = self.client.get("/cliente/?nome=Zé&tipo=aluno")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

    def test_listar_clientes_com_multiplos_filtros(self):
        # cria clientes de exemplo
        clientes = [
            {
                "cpf": "39410861977",
                "nome": "Alice Silva",
                "matricula": "2024001",
                "tipo": "aluno",
                "graduando": True,
                "pos_graduando": False,
                "bolsista": True,
            },
            {
                "cpf": "88451210031",
                "nome": "Bob Santos",
                "matricula": "2024002",
                "tipo": "professor",
                "graduando": False,
                "pos_graduando": False,
                "bolsista": False,
            },
            {
                "cpf": "36452746006",
                "nome": "Carol Pereira",
                "matricula": "2024003",
                "tipo": "aluno",
                "graduando": True,
                "pos_graduando": False,
                "bolsista": False,
            },
        ]

        for c in clientes:
            self.client.post("/cliente/", json=c)

        # filtro por tipo=aluno e graduando=True e bolsista=True
        response = self.client.get(
            "/cliente/", params={"tipo": "aluno", "graduando": True, "bolsista": True}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertIn("Alice", data[0]["nome"])


if __name__ == "__main__":
    unittest.main()
