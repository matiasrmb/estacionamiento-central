import unittest
from contextlib import contextmanager
from unittest.mock import patch

from controllers import config_controller


class FakeCursor:
    def __init__(self, fetchall_results=None):
        self.fetchall_results = list(fetchall_results or [])
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchall(self):
        if self.fetchall_results:
            return self.fetchall_results.pop(0)
        return []


@contextmanager
def fake_db_cursor(cursor):
    yield cursor


class ConfigControllerTests(unittest.TestCase):
    @patch.object(config_controller, "db_cursor")
    def test_actualizar_configuracion_inserta_o_actualiza_clave(self, db_cursor):
        cursor = FakeCursor()
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = config_controller.actualizar_configuracion("lavado_suv", 8000)

        self.assertTrue(resultado)
        db_cursor.assert_called_once_with(commit=True)
        query, params = cursor.executed[0]
        self.assertIn("INSERT INTO configuracion", query)
        self.assertIn("ON DUPLICATE KEY UPDATE", query)
        self.assertEqual(params, ("lavado_suv", "8000"))

    def test_obtener_valores_lavado_usa_configuracion_y_defaults(self):
        valores = config_controller.obtener_valores_lavado({"lavado_suv": "9000"})

        self.assertEqual(valores["lavado_citycar"]["valor"], 5000)
        self.assertEqual(valores["lavado_suv"]["valor"], 9000)
        self.assertEqual(valores["lavado_minibus"]["valor"], 25000)


if __name__ == "__main__":
    unittest.main()
