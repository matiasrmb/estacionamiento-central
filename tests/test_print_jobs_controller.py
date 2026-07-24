import unittest
from contextlib import contextmanager
from unittest.mock import patch

from controllers import print_jobs_controller


class FakeCursor:
    def __init__(self, fetchall_results=None, rowcount=0):
        self.fetchall_results = list(fetchall_results or [])
        self.rowcount = rowcount
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


class PrintJobsControllerTests(unittest.TestCase):
    @patch.object(print_jobs_controller, "db_cursor")
    def test_lista_solo_trabajos_en_error(self, db_cursor):
        jobs = [{"id": 8, "estado": "ERROR", "patente": "ABC123"}]
        cursor = FakeCursor(fetchall_results=[jobs])
        db_cursor.return_value = fake_db_cursor(cursor)

        result = print_jobs_controller.listar_trabajos_impresion_fallidos()

        self.assertEqual(result, jobs)
        db_cursor.assert_called_once_with(dictionary=True)
        query, params = cursor.executed[0]
        self.assertIn("FROM print_jobs", query)
        self.assertIn("WHERE estado = %s", query)
        self.assertEqual(params, ("ERROR",))

    @patch.object(print_jobs_controller, "db_cursor")
    def test_lista_fallidos_no_proyecta_el_payload(self, db_cursor):
        cursor = FakeCursor(fetchall_results=[[]])
        db_cursor.return_value = fake_db_cursor(cursor)

        print_jobs_controller.listar_trabajos_impresion_fallidos()

        query, _ = cursor.executed[0]
        selected_columns = query.split("FROM print_jobs", 1)[0]
        self.assertNotIn("payload_json", selected_columns.lower())

    @patch.object(print_jobs_controller, "db_cursor")
    def test_reintenta_solo_error_y_limpia_datos_de_bloqueo(self, db_cursor):
        cursor = FakeCursor(rowcount=1)
        db_cursor.return_value = fake_db_cursor(cursor)

        result = print_jobs_controller.reintentar_trabajo_impresion_fallido(8)

        self.assertTrue(result)
        db_cursor.assert_called_once_with(commit=True)
        query, params = cursor.executed[0]
        self.assertIn("estado = %s", query)
        self.assertIn("intentos = 0", query)
        self.assertIn("locked_at = NULL", query)
        self.assertIn("locked_by = NULL", query)
        self.assertIn("last_error = NULL", query)
        self.assertIn("next_retry_at = NULL", query)
        self.assertIn("updated_at = CURRENT_TIMESTAMP", query)
        self.assertIn("WHERE id_print_job = %s AND estado = %s", query)
        self.assertEqual(params, ("PENDIENTE", 8, "ERROR"))

    @patch.object(print_jobs_controller, "db_cursor")
    def test_reintento_falla_con_rowcount_cero_por_estado_obsoleto(self, db_cursor):
        cursor = FakeCursor(rowcount=0)
        db_cursor.return_value = fake_db_cursor(cursor)

        result = print_jobs_controller.reintentar_trabajo_impresion_fallido(8)

        self.assertFalse(result)
        query, params = cursor.executed[0]
        self.assertIn("WHERE id_print_job = %s AND estado = %s", query)
        self.assertEqual(params, ("PENDIENTE", 8, "ERROR"))


if __name__ == "__main__":
    unittest.main()
