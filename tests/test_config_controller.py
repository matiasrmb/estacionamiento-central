import unittest
from contextlib import contextmanager
from unittest.mock import patch

from controllers import config_controller


class FakeCursor:
    def __init__(self, fetchall_results=None, fetchone_results=None):
        self.fetchall_results = list(fetchall_results or [])
        self.fetchone_results = list(fetchone_results or [])
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchall(self):
        if self.fetchall_results:
            return self.fetchall_results.pop(0)
        return []

    def fetchone(self):
        if self.fetchone_results:
            return self.fetchone_results.pop(0)
        return None


class FailingConfigCursor(FakeCursor):
    def execute(self, query, params=None):
        if "FROM configuracion" in query:
            raise RuntimeError("config no disponible")
        super().execute(query, params)


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

    def test_print_jobs_pc_activos_usa_el_valor_predeterminado_y_respeta_desactivacion(self):
        self.assertTrue(config_controller.print_jobs_pc_activos({}))
        self.assertFalse(config_controller.print_jobs_pc_activos({"pc_print_jobs_activos": "0"}))

    def test_obtener_print_jobs_pc_activos_usa_cursor_operativo_y_valor_predeterminado(self):
        cursor = FakeCursor(fetchone_results=[None, {"valor": "0"}])

        self.assertTrue(config_controller.obtener_print_jobs_pc_activos(cursor))
        self.assertFalse(config_controller.obtener_print_jobs_pc_activos(cursor))
        self.assertEqual(cursor.executed[0][1], ("pc_print_jobs_activos",))

    def test_obtener_print_jobs_pc_activos_habilita_impresion_si_falla_la_lectura(self):
        self.assertTrue(config_controller.obtener_print_jobs_pc_activos(FailingConfigCursor()))


if __name__ == "__main__":
    unittest.main()
