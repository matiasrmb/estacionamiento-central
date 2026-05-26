import unittest
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import patch

from controllers import lavados_controller


class FakeCursor:
    def __init__(self, fetchone_results=None, fetchall_results=None):
        self.fetchone_results = list(fetchone_results or [])
        self.fetchall_results = list(fetchall_results or [])
        self.executed = []
        self.lastrowid = 55

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        if self.fetchone_results:
            return self.fetchone_results.pop(0)
        return None

    def fetchall(self):
        if self.fetchall_results:
            return self.fetchall_results.pop(0)
        return []


@contextmanager
def fake_db_cursor(cursor):
    yield cursor


class LavadosControllerTests(unittest.TestCase):
    @patch.object(lavados_controller, "asegurar_schema_lavados")
    @patch.object(lavados_controller, "obtener_categorias_lavado")
    @patch.object(lavados_controller, "db_cursor")
    def test_iniciar_lavado_crea_registro_y_marca_ingreso(
        self,
        db_cursor,
        obtener_categorias,
        asegurar_schema,
    ):
        cursor = FakeCursor(fetchone_results=[{
            "id_ingreso": 10,
            "id_vehiculo": 7,
            "patente": "ABC123",
            "en_lavado": 0,
        }])
        db_cursor.return_value = fake_db_cursor(cursor)
        obtener_categorias.return_value = {
            "lavado_suv": {"label": "SUV", "valor": 8000}
        }

        resultado = lavados_controller.iniciar_lavado(10, "lavado_suv", "admin")

        self.assertEqual(resultado["id_lavado"], 55)
        self.assertEqual(resultado["valor_lavado"], 8000)
        asegurar_schema.assert_called_once()
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("INSERT INTO lavados", consultas)
        self.assertIn("UPDATE ingresos SET en_lavado = 1", consultas)

    @patch.object(lavados_controller, "asegurar_schema_lavados")
    @patch.object(lavados_controller, "obtener_categorias_lavado")
    @patch.object(lavados_controller, "db_cursor")
    def test_iniciar_lavado_retorna_none_si_ingreso_ya_esta_en_lavado(
        self,
        db_cursor,
        obtener_categorias,
        asegurar_schema,
    ):
        cursor = FakeCursor(fetchone_results=[{
            "id_ingreso": 10,
            "id_vehiculo": 7,
            "patente": "ABC123",
            "en_lavado": 1,
        }])
        db_cursor.return_value = fake_db_cursor(cursor)
        obtener_categorias.return_value = {
            "lavado_suv": {"label": "SUV", "valor": 8000}
        }

        resultado = lavados_controller.iniciar_lavado(10, "lavado_suv", "admin")

        self.assertIsNone(resultado)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertNotIn("INSERT INTO lavados", consultas)

    @patch.object(lavados_controller, "asegurar_schema_lavados")
    @patch.object(lavados_controller, "db_cursor")
    def test_finalizar_lavado_cierra_registro_y_reactiva_ingreso(self, db_cursor, asegurar_schema):
        inicio = datetime(2026, 1, 1, 10, 0)
        cursor = FakeCursor(fetchone_results=[{
            "id_lavado": 55,
            "categoria_lavado": "lavado_suv",
            "valor_lavado": 8000,
            "fecha_hora_inicio": inicio,
        }])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = lavados_controller.finalizar_lavado(10, "admin")

        self.assertEqual(resultado["id_lavado"], 55)
        self.assertEqual(resultado["fecha_hora_inicio"], inicio)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("UPDATE lavados", consultas)
        self.assertIn("UPDATE ingresos SET en_lavado = 0", consultas)

    @patch.object(lavados_controller, "obtener_lavados_por_ingreso")
    def test_calcular_minutos_lavado_suma_intervalos(self, obtener_lavados):
        obtener_lavados.return_value = [
            {
                "fecha_hora_inicio": datetime(2026, 1, 1, 10, 0),
                "fecha_hora_fin": datetime(2026, 1, 1, 10, 20),
            },
            {
                "fecha_hora_inicio": datetime(2026, 1, 1, 11, 0),
                "fecha_hora_fin": datetime(2026, 1, 1, 11, 15),
            },
        ]

        minutos = lavados_controller.calcular_minutos_lavado(10)

        self.assertEqual(minutos, 35)


if __name__ == "__main__":
    unittest.main()
