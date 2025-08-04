import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.models.models import Compra
from app.models.db_setup import engine
from sqlalchemy.orm import Session
from datetime import time

client = TestClient(app)


class AuthTestCase(unittest.TestCase):
    def tearDown(self):
        self.db.query(Compra).delete()
        self.db.commit()
        self.db.close()

    def setUp(self):
        self.client = client
        self.db: Session = Session(bind=engine)
        self.db.query(Compra).delete()
        self.db.commit()

        compra_info = Compra(
            id_usuario=1234, horario=time(10, 50), local="ufcg", forma_pagamento="pix"
        )

        self.db.add(compra_info)
        self.db.commit()
        self.db.refresh(compra_info)

    def test_cadastra_sucesso(self):
        payload = {
            "usuario_id": 5678,
            "horario": time(11, 20),
            "local": "ufcg",
            "forma_pagamento": "dinheiro",
        }

        response = self.client.post("/cadastra-compra/", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["horario"], payload["horario"])

    def test_busca_compras(self):
        response = client.get("/retorna-compras/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIsInstance(data, list)
        horarios = [compra["horario"] for compra in data]
        self.assertIn("10:50", horarios)

    def test_busca_compras_not_found(self):
        self.db.query(Compra).delete()
        self.db.commit()
        self.tearDown()
        response = self.client.get("/retorna-compras/")
        self.assertEqual(response.status_code, 404)
        assert response.json() == {"detail": "Nenhuma compra cadastrada no sistema"}

    def test_filtra_compras(self):
        payload = {
            "usuario_id": 5678,
            "horario": time(11, 20),
            "local": "ufcg",
            "forma_pagamento": "dinheiro",
        }
        self.client.post("/cadastra-compra/", json=payload)
        response = client.get("/filtra-compras/", params={"forma_pagamento": "pix"})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIsInstance(data, list)
        formas_pagamento = [compra["forma_pagamento"] for compra in data]
        self.assertIn("pix", formas_pagamento)

    def test_filtra_compras_not_found(self):
        response = self.client.get(
            "/filtra-compras/", params={"forma_pagamento": "dinheiro"}
        )
        self.assertEqual(response.status_code, 404)
        assert response.json() == {
            "detail": "Nenhuma compra encontrada com os filtros fornecidos"
        }

    def test_filtra_compras_not_found_bd_vazio(self):
        self.db.query(Compra).delete()
        self.db.commit()
        self.tearDown()
        response = self.client.get("/filtra-compras/")
        self.assertEqual(response.status_code, 404)
        assert response.json() == {
            "detail": "Nenhuma compra encontrada com os filtros fornecidos"
        }
