import unittest
import io
import polars as pl
from fastapi.testclient import TestClient
from app.core.seguranca import criptografa_cpf, hash_cpf
from app.main import app
from app.models.models import Compra
from app.models.models import Cliente
from app.models.db_setup import engine
from sqlalchemy.orm import Session
from datetime import datetime


client = TestClient(app)
cliente = Cliente(
    cpf_hash=hash_cpf("39410861977"),
    cpf_cript=criptografa_cpf("39410861977"),
    nome="Fulano",
    matricula="20249999",
    tipo="aluno",
    graduando=False,
    pos_graduando=True,
    bolsista=False,
)


class CompraTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db: Session = Session(bind=engine)
        db_cliente = (
            cls.db.query(Cliente).filter_by(cpf_hash=hash_cpf("39410861977")).first()
        )
        if not db_cliente:
            cls.cliente = Cliente(
                cpf_hash=hash_cpf("39410861977"),
                cpf_cript=criptografa_cpf("39410861977"),
                nome="Fulano",
                matricula="20249999",
                tipo="aluno",
                graduando=False,
                pos_graduando=True,
                bolsista=False,
            )
            cls.db.add(cls.cliente)
            cls.db.commit()
            cls.db.refresh(cls.cliente)
        else:
            cls.cliente = db_cliente

    @classmethod
    def tearDownClass(cls):
        cls.db.delete(cls.cliente)
        cls.db.commit()
        cls.db.close()

    def setUp(self):
        self.db: Session = Session(bind=engine)
        self.client = client
        self.db.query(Compra).delete()
        self.db.commit()

    def tearDown(self):
        self.db.query(Compra).delete()
        self.db.commit()
        self.db.close()

    def test_cadastra_sucesso(self):
        payload = {
            "usuario_id": 1,
            "horario": datetime(2025, 6, 20, 11, 20).isoformat(),
            "local": "ufcg",
            "forma_pagamento": "dinheiro",
        }
        response = self.client.post("/compra/", json=payload)
        self.assertEqual(response.status_code, 201)

        info = response.json()
        self.assertEqual(info, {"message": "Compra cadastrada com sucesso"})

    def generate_csv_bytes(self, headers: list[str], rows: list[dict]) -> bytes:
        tabela = pl.DataFrame(rows)[headers]
        buf = io.BytesIO()
        tabela.write_csv(buf)
        return buf.getvalue()

    def test_cadastra_csv_sucesso(self):
        headers = [
            "usuario_id",
            "horario",
            "local",
            "forma_pagamento",
        ]
        rows = [
            {
                "usuario_id": 5678,
                "horario": "2025-04-12T10:50:00",
                "local": "ufcg",
                "forma_pagamento": "dinheiro",
            },
        ]
        csv_bytes = self.generate_csv_bytes(headers, rows)

        response = self.client.post(
            "/compra/csv",
            files={"arquivo": ("compras.csv", csv_bytes, "text/csv")},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "1 compra(s) cadastrada(s) com sucesso.")

        compra = self.db.query(Compra).filter_by(forma_pagamento="dinheiro").first()
        self.assertIsNotNone(compra)

    def test_cadastra_csv_extensao_invalida(self):
        csv_bytes = b"qualquer,conteudo\n"
        response = self.client.post(
            "/compra/csv",
            files={"arquivo": ("compras.txt", csv_bytes, "text/plain")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("O arquivo deveria ser CSV.", response.json()["detail"])

    def test_cadastra_csv_colunas_faltando(self):
        headers = ["usuario_id", "horario", "local"]
        rows = [
            {
                "usuario_id": 5678,
                "horario": "2025-04-12T10:50:00",
                "local": "ufcg",
            }
        ]
        csv_bytes = self.generate_csv_bytes(headers, rows)

        response = self.client.post(
            "/compra/csv",
            files={"arquivo": ("compras.csv", csv_bytes, "text/csv")},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn(
            "O CSV não contém as colunas necessárias.", response.json()["detail"]
        )

    def test_busca_compras(self):
        compra = Compra(
            usuario_id=self.cliente.usuario_id,
            horario=datetime(2025, 4, 12, 10, 50),
            local="ufcg",
            forma_pagamento="pix",
        )
        self.db.add(compra)
        self.db.commit()

        response = client.get("/compra/")
        self.assertEqual(response.status_code, 200)
        info = response.json()
        self.assertIsInstance(info, list)
        horarios = [compra["horario"] for compra in info]
        self.assertIn("2025-04-12T10:50:00", horarios)

    def test_busca_compras_not_found(self):
        self.db.query(Compra).delete()
        self.db.commit()
        self.tearDown()
        response = self.client.get("/compra/")
        self.assertEqual(response.status_code, 404)
        assert response.json() == {
            "detail": "Nenhuma compra encontrada com os filtros fornecidos"
        }

    def test_filtra_compras(self):
        compras = [
            {
                "usuario_id": self.cliente.usuario_id,
                "horario": datetime(2025, 6, 20, 11, 20).isoformat(),
                "local": "ufcg",
                "forma_pagamento": "dinheiro",
            },
            {
                "usuario_id": self.cliente.usuario_id,
                "horario": datetime(2023, 4, 13, 12, 00, 0).isoformat(),
                "local": "ufcg",
                "forma_pagamento": "pix",
            },
        ]

        for i in compras:
            self.client.post("/compra/", json=i)

        response = self.client.get("/compra/", params={"forma_pagamento": "pix"})
        self.assertEqual(response.status_code, 200)
        info = response.json()
        self.assertEqual(len(info), 1)
        self.assertEqual(info[0]["horario"], "2023-04-13T12:00:00")

    def test_filtra_compras_not_found(self):
        response = self.client.get("/compra/", params={"forma_pagamento": "dinheiro"})
        self.assertEqual(response.status_code, 404)
        assert response.json() == {
            "detail": "Nenhuma compra encontrada com os filtros fornecidos"
        }

    def test_filtra_compras_not_found_bd_vazio(self):
        self.db.query(Compra).delete()
        self.db.commit()
        self.tearDown()
        response = self.client.get("/compra/")
        self.assertEqual(response.status_code, 404)
        assert response.json() == {
            "detail": "Nenhuma compra encontrada com os filtros fornecidos"
        }


if __name__ == "__main__":
    unittest.main()
