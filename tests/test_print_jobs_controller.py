import unittest
from contextlib import contextmanager
from unittest.mock import patch

from controllers import print_jobs_controller


class FakeCursor:
    def __init__(self, fetchall_results=None, fetchone_results=None, rowcount=0, lastrowids=None):
        self.fetchall_results = list(fetchall_results or [])
        self.fetchone_results = list(fetchone_results or [])
        self.rowcount = rowcount
        self.lastrowids = list(lastrowids or [])
        self.lastrowid = None
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))
        if self.lastrowids:
            self.lastrowid = self.lastrowids.pop(0)

    def fetchall(self):
        if self.fetchall_results:
            return self.fetchall_results.pop(0)
        return []

    def fetchone(self):
        if self.fetchone_results:
            return self.fetchone_results.pop(0)
        return None


@contextmanager
def fake_db_cursor(cursor):
    yield cursor


class PrintJobsControllerTests(unittest.TestCase):
    @patch.object(print_jobs_controller, "db_cursor")
    def test_lista_trabajos_en_error_y_revision_manual(self, db_cursor):
        jobs = [
            {"id": 8, "estado": "ERROR", "patente": "ABC123"},
            {"id": 9, "estado": "REVISION_MANUAL", "patente": "XYZ789"},
        ]
        cursor = FakeCursor(fetchall_results=[jobs])
        db_cursor.return_value = fake_db_cursor(cursor)

        result = print_jobs_controller.listar_trabajos_impresion_fallidos()

        self.assertEqual(result, jobs)
        db_cursor.assert_called_once_with(dictionary=True)
        query, params = cursor.executed[0]
        self.assertIn("FROM print_jobs", query)
        self.assertIn("estado IN (%s, %s)", query)
        self.assertIn("estado", query)
        self.assertEqual(params, ("ERROR", "REVISION_MANUAL"))

    @patch.object(print_jobs_controller, "db_cursor")
    def test_lista_fallidos_no_proyecta_el_payload(self, db_cursor):
        cursor = FakeCursor(fetchall_results=[[]])
        db_cursor.return_value = fake_db_cursor(cursor)

        print_jobs_controller.listar_trabajos_impresion_fallidos()

        query, _ = cursor.executed[0]
        selected_columns = query.split("FROM print_jobs", 1)[0]
        self.assertNotIn("payload_json", selected_columns.lower())

    @patch.object(print_jobs_controller, "db_cursor")
    def test_lista_impresos_no_proyecta_el_payload(self, db_cursor):
        cursor = FakeCursor(fetchall_results=[[]])
        db_cursor.return_value = fake_db_cursor(cursor)

        print_jobs_controller.listar_trabajos_impresion_impresos()

        query, params = cursor.executed[0]
        selected_columns = query.split("FROM print_jobs", 1)[0]
        self.assertNotIn("payload_json", selected_columns.lower())
        self.assertEqual(params, ("IMPRESO", 50))

    def test_reimpresion_rechaza_motivo_vacio(self):
        with self.assertRaisesRegex(ValueError, "motivo"):
            print_jobs_controller.crear_reimpresion_trabajo_impresion(8, "operador", "  ")

    def test_reimpresion_rechaza_operador_vacio(self):
        with self.assertRaisesRegex(ValueError, "operador"):
            print_jobs_controller.crear_reimpresion_trabajo_impresion(8, " ", "Ticket ilegible")

    @patch.object(print_jobs_controller, "db_cursor")
    def test_reimpresion_crea_pendiente_y_auditoria_sin_mutar_origen(self, db_cursor):
        source = {
            "id_print_job": 8,
            "tipo": "TICKET_SALIDA",
            "destino": "PC_PDF",
            "id_ingreso": 4,
            "patente": "ABC123",
            "payload_json": '{"kind":"TICKET_SALIDA"}',
        }
        cursor = FakeCursor(fetchone_results=[source, None], lastrowids=[None, None, 19, 7])
        db_cursor.return_value = fake_db_cursor(cursor)

        result = print_jobs_controller.crear_reimpresion_trabajo_impresion(8, "operador", "Ticket ilegible")

        self.assertEqual(result, {"new_print_job_id": 19, "audit_id": 7})
        db_cursor.assert_called_once_with(dictionary=True, commit=True)
        select_query, select_params = cursor.executed[0]
        active_reprint_query, active_reprint_params = cursor.executed[1]
        insert_query, insert_params = cursor.executed[2]
        audit_query, audit_params = cursor.executed[3]
        self.assertIn("estado = %s", select_query)
        self.assertIn("FOR UPDATE", select_query)
        self.assertEqual(select_params, (8, "IMPRESO"))
        self.assertIn("FROM print_job_reprints", active_reprint_query)
        self.assertIn("INNER JOIN print_jobs", active_reprint_query)
        self.assertEqual(active_reprint_params, (8, "PENDIENTE", "IMPRIMIENDO", "REVISION_MANUAL"))
        self.assertIn("INSERT INTO print_jobs", insert_query)
        self.assertEqual(insert_params[4], source["payload_json"])
        self.assertEqual(insert_params[5], "PENDIENTE")
        self.assertTrue(insert_params[6].startswith("reprint:8:"))
        self.assertIn("INSERT INTO print_job_reprints", audit_query)
        self.assertEqual(audit_params, (8, 19, "operador", "Ticket ilegible"))
        self.assertNotIn("UPDATE print_jobs", "\n".join(query for query, _ in cursor.executed))

    @patch.object(print_jobs_controller, "db_cursor")
    def test_reimpresion_activa_bloquea_duplicado_sin_crear_trabajo_ni_auditoria(self, db_cursor):
        source = {"id_print_job": 8}
        cursor = FakeCursor(fetchone_results=[source, {"new_print_job_id": 19}])
        db_cursor.return_value = fake_db_cursor(cursor)

        result = print_jobs_controller.crear_reimpresion_trabajo_impresion(8, "operador", "Ticket ilegible")

        self.assertFalse(result)
        self.assertEqual(len(cursor.executed), 2)
        active_reprint_query, active_reprint_params = cursor.executed[1]
        self.assertIn("FROM print_job_reprints", active_reprint_query)
        self.assertIn("INNER JOIN print_jobs", active_reprint_query)
        self.assertEqual(active_reprint_params, (8, "PENDIENTE", "IMPRIMIENDO", "REVISION_MANUAL"))
        executed_queries = "\n".join(query for query, _ in cursor.executed)
        self.assertNotIn("INSERT INTO print_jobs", executed_queries)
        self.assertNotIn("INSERT INTO print_job_reprints", executed_queries)

    @patch.object(print_jobs_controller, "db_cursor")
    def test_reimpresion_impresa_previa_permite_nueva_reimpresion(self, db_cursor):
        source = {
            "id_print_job": 8,
            "tipo": "TICKET_SALIDA",
            "destino": "PC_PDF",
            "id_ingreso": 4,
            "patente": "ABC123",
            "payload_json": '{"kind":"TICKET_SALIDA"}',
        }
        cursor = FakeCursor(fetchone_results=[source, None], lastrowids=[None, None, 20, 8])
        db_cursor.return_value = fake_db_cursor(cursor)

        result = print_jobs_controller.crear_reimpresion_trabajo_impresion(8, "operador", "Ticket ilegible")

        self.assertEqual(result, {"new_print_job_id": 20, "audit_id": 8})
        active_reprint_query, active_reprint_params = cursor.executed[1]
        self.assertIn("reprint_job.estado IN (%s, %s, %s)", active_reprint_query)
        self.assertEqual(active_reprint_params, (8, "PENDIENTE", "IMPRIMIENDO", "REVISION_MANUAL"))
        self.assertIn("INSERT INTO print_jobs", cursor.executed[2][0])
        self.assertIn("INSERT INTO print_job_reprints", cursor.executed[3][0])

    @patch.object(print_jobs_controller, "db_cursor")
    def test_reimpresion_no_acepta_error_ni_revision_manual(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[None, None])
        db_cursor.side_effect = lambda **_kwargs: fake_db_cursor(cursor)

        self.assertIsNone(print_jobs_controller.crear_reimpresion_trabajo_impresion(8, "operador", "Duplicado"))
        self.assertIsNone(print_jobs_controller.crear_reimpresion_trabajo_impresion(9, "operador", "Duplicado"))

        self.assertEqual(len(cursor.executed), 2)
        for query, params in cursor.executed:
            self.assertIn("estado = %s", query)
            self.assertEqual(params[1], "IMPRESO")

    @patch.object(print_jobs_controller, "db_cursor")
    def test_reintenta_solo_error_y_limpia_datos_de_bloqueo(self, db_cursor):
        cursor = FakeCursor(rowcount=1)
        db_cursor.return_value = fake_db_cursor(cursor)

        result = print_jobs_controller.reintentar_trabajo_impresion_fallido(8)

        self.assertTrue(result)
        db_cursor.assert_called_once_with(commit=True)
        query, params = cursor.executed[0]
        self.assertIn("estado = %s", query)
        self.assertNotIn("intentos = 0", query)
        self.assertIn("locked_at = NULL", query)
        self.assertIn("locked_by = NULL", query)
        self.assertIn("last_error = NULL", query)
        self.assertIn("next_retry_at = NULL", query)
        self.assertIn("updated_at = CURRENT_TIMESTAMP", query)
        self.assertIn("WHERE id_print_job = %s AND estado = %s", query)
        self.assertEqual(params, ("PENDIENTE", 8, "ERROR"))

    @patch.object(print_jobs_controller, "db_cursor")
    def test_reintento_manual_solo_rehabilita_revision_manual(self, db_cursor):
        cursor = FakeCursor(rowcount=1)
        db_cursor.return_value = fake_db_cursor(cursor)

        result = print_jobs_controller.reintentar_trabajo_impresion_revision_manual(8)

        self.assertTrue(result)
        query, params = cursor.executed[0]
        self.assertIn("estado = %s", query)
        self.assertIn("intentos = 0", query)
        self.assertIn("next_retry_at = NULL", query)
        self.assertIn("last_error = NULL", query)
        self.assertEqual(params, ("PENDIENTE", 8, "REVISION_MANUAL"))

    @patch.object(print_jobs_controller, "db_cursor")
    def test_reintento_falla_con_rowcount_cero_por_estado_obsoleto(self, db_cursor):
        cursor = FakeCursor(rowcount=0)
        db_cursor.return_value = fake_db_cursor(cursor)

        result = print_jobs_controller.reintentar_trabajo_impresion_fallido(8)

        self.assertFalse(result)
        query, params = cursor.executed[0]
        self.assertIn("WHERE id_print_job = %s AND estado = %s", query)
        self.assertEqual(params, ("PENDIENTE", 8, "ERROR"))

    @patch.object(print_jobs_controller, "db_cursor")
    def test_reintento_manual_falla_con_rowcount_cero_por_estado_obsoleto(self, db_cursor):
        cursor = FakeCursor(rowcount=0)
        db_cursor.return_value = fake_db_cursor(cursor)

        result = print_jobs_controller.reintentar_trabajo_impresion_revision_manual(8)

        self.assertFalse(result)
        query, params = cursor.executed[0]
        self.assertIn("WHERE id_print_job = %s AND estado = %s", query)
        self.assertEqual(params, ("PENDIENTE", 8, "REVISION_MANUAL"))


if __name__ == "__main__":
    unittest.main()
