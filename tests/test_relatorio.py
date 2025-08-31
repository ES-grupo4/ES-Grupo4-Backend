import unittest
from datetime import date, datetime, time
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.seguranca import gerar_hash, criptografa_cpf, descriptografa_cpf
from app.main import app
from app.models.models import Funcionario, Cliente, Compra, InformacoesGerais, Usuario
from app.models.db_setup import engine

client = TestClient(app)


class RelatorioTestCase(unittest.TestCase):
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

        # Criar dados de teste para o relatório
        self.criar_dados_teste()

    def criar_dados_teste(self):
        """Cria dados de teste para o relatório"""
        # Limpar dados existentes
        self.db.query(Compra).delete()
        self.db.query(Cliente).delete()

        # Criar clientes de diferentes tipos
        clientes = [
            {
                "cpf_hash": gerar_hash("70199685037"),
                "cpf_cript": criptografa_cpf("70199685037"),
                "nome": "Cliente Externo",
                "matricula": "",
                "tipo": "externo",
                "graduando": False,
                "pos_graduando": False,
                "bolsista": False,
            },
            {
                "cpf_hash": gerar_hash("87928349060"),
                "cpf_cript": criptografa_cpf("87928349060"),
                "nome": "Professor Teste",
                "matricula": "202400001",
                "tipo": "professor",
                "graduando": False,
                "pos_graduando": False,
                "bolsista": False,
            },
            {
                "cpf_hash": gerar_hash("47364363017"),
                "cpf_cript": criptografa_cpf("47364363017"),
                "nome": "Técnico Teste",
                "tipo": "tecnico",
                "matricula": "",
                "graduando": False,
                "pos_graduando": False,
                "bolsista": False,
            },
            {
                "cpf_hash": gerar_hash("72050228007"),
                "cpf_cript": criptografa_cpf("72050228007"),
                "nome": "Aluno Graduação",
                "tipo": "aluno",
                "matricula": "202400002",
                "graduando": True,
                "pos_graduando": False,
                "bolsista": False,
            },
            {
                "cpf_hash": gerar_hash("90464227046"),
                "cpf_cript": criptografa_cpf("90464227046"),
                "nome": "Aluno Pós",
                "tipo": "aluno",
                "matricula": "202400003",
                "graduando": False,
                "pos_graduando": True,
                "bolsista": True,
            },
            {
                "cpf_hash": gerar_hash("83815004004"),
                "cpf_cript": criptografa_cpf("83815004004"),
                "nome": "Aluno Ambos",
                "tipo": "aluno",
                "matricula": "202400004",
                "graduando": True,
                "pos_graduando": True,
                "bolsista": False,
            },
        ]

        for cliente_data in clientes:
            cliente = Cliente(**cliente_data)
            self.db.add(cliente)

        self.db.commit()

        info_gerais = InformacoesGerais(
            fim_almoco=time(14, 0, 0),
            fim_jantar=time(20, 0, 0),
            inicio_almoco=time(12, 30, 0),
            inicio_jantar=time(17, 0, 0),
            nome_empresa="Fulano de Sal",
            preco_almoco=12,
            preco_jantar=10,
            preco_meia_almoco=6,
            preco_meia_jantar=5,
        )
        self.db.add(info_gerais)

        compras = [
            {
                "usuario_id": 1,  # cliente externo
                "horario": datetime(2025, 8, 15, 10, 0, 0),
                "local": "humanas",
                "forma_pagamento": "pix",
                "preco_compra": 1196,
            },
            {
                "usuario_id": 2,  # professor
                "horario": datetime(2025, 8, 20, 14, 0, 0),
                "local": "exatas",
                "forma_pagamento": "dinheiro",
                "preco_compra": 1196,
            },
            {
                "usuario_id": 4,  # aluno graduação
                "horario": datetime(2025, 8, 25, 16, 0, 0),
                "local": "humanas",
                "forma_pagamento": "cartao",
                "preco_compra": 596,
            },
        ]

        for compra_data in compras:
            compra = Compra(**compra_data)
            self.db.add(compra)

        self.db.commit()

    def cria_funcionario(self, dados=None):
        dados = {
            "cpf": "79920205451",
            "nome": "Funcionario Teste",
            "senha": "John123!",
            "email": "funcionario@teste.com",
            "tipo": "funcionario",
            "data_entrada": "2024-08-01",
        }
        response = client.post("/funcionario/", json=dados, headers=self.auth_headers)
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

    def tearDown(self):
        # Limpar dados de teste
        self.db.query(Compra).delete()
        self.db.query(Cliente).delete()
        self.db.query(Funcionario).delete()
        self.db.query(InformacoesGerais).delete()
        self.db.query(Usuario).delete()

        # Manter o admin para outros testes
        admin = (
            self.db.query(Funcionario)
            .filter_by(cpf_hash=gerar_hash("19896507406"))
            .first()
        )
        if admin:
            self.db.delete(admin)

        # Manter os clientes para outros testes
        clientes = [
            "70199685037",
            "87928349060",
            "47364363017",
            "72050228007",
            "90464227046",
            "83815004004",
        ]
        for cliente in clientes:
            self.db.query(Usuario).filter_by(cpf_hash=gerar_hash(cliente)).first()

        self.db.commit()
        self.db.close()

    def test_relatorio_estrutura_detalhada(self):
        response = client.get("/relatorio/2024/8", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        keys_esperadas = {
            "nome_empresa",
            "faturamento_bruto_mensal",
            "clientes_registrados",
            "funcionarios_ativos",
            "administradores_ativos",
            "desativados",
            "funcionarios_adicionados_mes",
            "compras_por_tipo",
        }
        self.assertEqual(set(data.keys()), keys_esperadas)

        clientes_keys = {"total", "externos", "professores", "tecnicos", "alunos"}
        self.assertEqual(set(data["clientes_registrados"].keys()), clientes_keys)

        alunos_keys = {"total", "pos_graduacao", "em_graduacao", "ambos", "bolsistas"}
        self.assertEqual(
            set(data["clientes_registrados"]["alunos"].keys()), alunos_keys
        )

        self.assertEqual(set(data["compras_por_tipo"].keys()), clientes_keys)
        self.assertEqual(set(data["compras_por_tipo"]["alunos"].keys()), alunos_keys)

    def test_relatorio_mes_valido_com_dados(self):
        response = client.get("/relatorio/2025/8", headers=self.auth_headers)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verificar estrutura básica do relatório
        self.assertIn("nome_empresa", data)
        self.assertIn("faturamento_bruto_mensal", data)
        self.assertIn("clientes_registrados", data)
        self.assertIn("funcionarios_ativos", data)
        self.assertIn("administradores_ativos", data)
        self.assertIn("desativados", data)
        self.assertIn("funcionarios_adicionados_mes", data)
        self.assertIn("compras_por_tipo", data)

        # Verificar valores específicos
        self.assertEqual(data["faturamento_bruto_mensal"], 2988)

        # Verificar clientes registrados
        clientes = data["clientes_registrados"]
        self.assertEqual(clientes["total"], 6)
        self.assertEqual(clientes["externos"], 1)
        self.assertEqual(clientes["professores"], 1)
        self.assertEqual(clientes["tecnicos"], 1)
        self.assertEqual(clientes["alunos"]["total"], 3)
        self.assertEqual(clientes["alunos"]["em_graduacao"], 1)
        self.assertEqual(clientes["alunos"]["pos_graduacao"], 1)
        self.assertEqual(clientes["alunos"]["ambos"], 1)
        self.assertEqual(clientes["alunos"]["bolsistas"], 1)

        # Verificar Funcionarios
        self.assertEqual(data["funcionarios_ativos"], 0)
        self.assertEqual(data["administradores_ativos"], 1)
        self.assertEqual(data["desativados"], 0)
        self.assertEqual(data["funcionarios_adicionados_mes"], 1)

        # Verificar compras por tipo
        compras = data["compras_por_tipo"]
        self.assertEqual(compras["total"], 2)
        self.assertEqual(compras["externos"], 1)
        self.assertEqual(compras["professores"], 0)
        self.assertEqual(compras["tecnicos"], 1)
        self.assertEqual(compras["alunos"]["total"], 0)
        self.assertEqual(compras["alunos"]["em_graduacao"], 0)

    def test_relatorio_mes_sem_dados(self):
        response = client.get("/relatorio/2024/1", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["faturamento_bruto_mensal"], 0)
        self.assertEqual(data["compras_por_tipo"]["total"], 0)
        self.assertEqual(data["clientes_registrados"]["total"], 6)

    def test_relatorio_mes_invalido(self):
        response = client.get("/relatorio/2024/13", headers=self.auth_headers)
        self.assertEqual(response.status_code, 422)

    def test_relatorio_ano_invalido(self):
        response = client.get("/relatorio/1899/8", headers=self.auth_headers)
        self.assertEqual(response.status_code, 422)

    def test_relatorio_sem_autenticacao(self):
        response = client.get("/relatorio/2024/8")
        self.assertEqual(response.status_code, 403)

    def test_relatorio_com_funcionario_permissao(self):
        self.cria_funcionario()
        self.login_funcionario()

        response = client.get(
            "/relatorio/2024/8",
            headers=self.auth_headers_funcionario,
        )
        self.assertEqual(response.status_code, 200)
