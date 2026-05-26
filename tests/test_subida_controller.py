import unittest
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import patch

from controllers import subida_controller


class FakeCursor:
    def __init__(self, fetchone_results=None):
        self.fetchone_results = list(fetchone_results or [])
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        if self.fetchone_results:
            return self.fetchone_results.pop(0)
        return None


@contextmanager
def fake_db_cursor(cursor):
    yield cursor


class SubidaControllerTests(unittest.TestCase):
    @patch.object(subida_controller, "db_cursor")
    def test_crear_subida_temporal_desactiva_anterior_e_inserta_nueva(self, db_cursor):
        cursor = FakeCursor()
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = subida_controller.crear_subida_temporal("10:00", "12:00", 200)

        self.assertTrue(resultado)
        db_cursor.assert_called_once_with(commit=True)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("UPDATE subida_precios SET activa = 0", consultas)
        self.assertIn("INSERT INTO subida_precios", consultas)

    @patch.object(subida_controller, "db_cursor")
    def test_obtener_subida_activa_retorna_ultima_subida_activa(self, db_cursor):
        subida = {"id_subida": 3, "monto_adicional": 200, "activa": 1}
        cursor = FakeCursor(fetchone_results=[subida])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = subida_controller.obtener_subida_activa()

        self.assertEqual(resultado, subida)
        db_cursor.assert_called_once_with(dictionary=True)

    def test_calcular_minutos_en_subida_en_rango_normal(self):
        ingreso = datetime(2026, 1, 1, 10, 30)
        salida = datetime(2026, 1, 1, 11, 30)

        minutos = subida_controller.calcular_minutos_en_subida(ingreso, salida, "10:00", "11:00")

        self.assertEqual(minutos, 30)

    def test_calcular_minutos_en_subida_sin_cruce(self):
        ingreso = datetime(2026, 1, 1, 8, 0)
        salida = datetime(2026, 1, 1, 9, 0)

        minutos = subida_controller.calcular_minutos_en_subida(ingreso, salida, "10:00", "11:00")

        self.assertEqual(minutos, 0)


if __name__ == "__main__":
    unittest.main()
