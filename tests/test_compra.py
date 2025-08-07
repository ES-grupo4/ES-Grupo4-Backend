import unittest
import io
import polars as pl
from fastapi.testclient import TestClient
from app.main import app
from app.models.models import Compra
from app.models.models import Cliente
from app.models.db_setup import engine
from sqlalchemy.orm import Session
from datetime import datetime

client = TestClient(app)


class CompraTestCase(unittest.TestCase):
    def tearDown(self):
        self.db.query(Compra).delete()
        self.db.commit()
        self.db.close()

    def setUp(self):
        self.client = client
        self.db: Session = Session(bind=engine)
        self.db.query(Compra).delete()
        self.db.commit()

        cliente_info = Cliente(
            cpf="99999999999",
            nome="Fulano",
            matricula="20249999",
            tipo="aluno",
            graduando=False,
            pos_graduando=True,
            bolsista=False,
        )

        compra_info = Compra(
            usuario_id=1,
            horario=datetime(2025, 4, 12, 10, 50),
            local="ufcg",
            forma_pagamento="pix",
        )

        self.db.add(cliente_info)
        self.db.commit()
        self.db.refresh(cliente_info)

        self.db.add(compra_info)
        self.db.commit()
        self.db.refresh(compra_info)

    def test_cadastra_sucesso(self):
        payload = {
            "usuario_id": 1,
            "horario": datetime(2025, 6, 20, 11, 20),
            "local": "ufcg",
            "forma_pagamento": "dinheiro",
        }

        response = self.client.post("/compra/cadastra-compra/", data=payload)
        self.assertEqual(response.status_code, 201)

        info = response.json()
        self.assertEqual(info["horario"], payload["horario"])
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
            "/compra/cadastra-compra-csv/",
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
            "/compra/cadastra-compra-csv/",
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
            "/compra/cadastra-compra-csv",
            files={"arquivo": ("compras.csv", csv_bytes, "text/csv")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "O CSV não contém as colunas necessárias.", response.json()["detail"]
        )

    def test_busca_compras(self):
        response = client.get("/compra/retorna-compras/")
        self.assertEqual(response.status_code, 200)

        info = response.json()
        self.assertIsInstance(info, list)
        horarios = [compra["horario"] for compra in info]
        self.assertIn("2025-04-12T10:50:00", horarios)

    def test_busca_compras_not_found(self):
        self.db.query(Compra).delete()
        self.db.commit()
        self.tearDown()
        response = self.client.get("/compra/retorna-compras/")
        self.assertEqual(response.status_code, 404)
        assert response.json() == {"detail": "Nenhuma compra cadastrada no sistema"}

    def test_filtra_compras(self):
        compras = [
            {
                "usuario_id": 1,
                "horario": datetime(2025, 6, 20, 11, 20),
                "local": "ufcg",
                "forma_pagamento": "dinheiro",
            },
            {
                "usuario_id": 1,
                "horario": datetime(2025, 4, 13, 12, 00),
                "local": "ufcg",
                "forma_pagamento": "pix",
            },
        ]

        for i in compras:
            self.client.post("/compra/cadastra-compra/", data=i)

        response = self.client.get(
            "/compra/filtra-compras/", params={"forma_pagamento": "pix"}
        )
        self.assertEqual(response.status_code, 200)
        info = response.json()
        self.assertEqual(len(info), 1)
        self.assertEqual(info[1]["horario"], "2025-04-13T12:00:00")

    def test_filtra_compras_not_found(self):
        response = self.client.get(
            "/compra/filtra-compras/", params={"forma_pagamento": "dinheiro"}
        )
        self.assertEqual(response.status_code, 404)
        assert response.json() == {
            "detail": "Nenhuma compra encontrada com os filtros fornecidos"
        }

    def test_filtra_compras_not_found_bd_vazio(self):
        self.db.query(Compra).delete()
        self.db.commit()
        self.tearDown()
        response = self.client.get("/compra/filtra-compras/")
        self.assertEqual(response.status_code, 404)
        assert response.json() == {
            "detail": "Nenhuma compra encontrada com os filtros fornecidos"
        }


if __name__ == "__main__":
    unittest.main()
