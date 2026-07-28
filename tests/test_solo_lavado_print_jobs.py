import json
import unittest
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import patch

from controllers import operaciones_servicio_controller
from utils import db as db_utils
from utils.print_jobs import solo_lavado_idempotency_key


class FakeCursor:
    def __init__(self, operation):
        self.operation = operation
        self.executed = []
        self.closed = False

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self.operation

    def close(self):
        self.closed = True


class FailingPrintJobCursor(FakeCursor):
    def execute(self, query, params=None):
        super().execute(query, params)
        if "INSERT INTO print_jobs" in query:
            raise RuntimeError("print job unavailable")


class FailingConfigLookupCursor(FakeCursor):
    def execute(self, query, params=None):
        if "FROM configuracion" in query:
            raise RuntimeError("config no disponible")
        super().execute(query, params)


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_instance = cursor
        self.committed = False
        self.rolled_back = False

    def cursor(self, *args, **kwargs):
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass


@contextmanager
def fake_db_cursor(cursor):
    yield cursor


class SoloLavadoPrintJobTests(unittest.TestCase):
    def setUp(self):
        self.operation = {
            "id_operacion_servicio": 31,
            "patente": "ABC123",
            "tipo_vehiculo_lavado_snapshot": "SUV",
            "valor_lavado_snapshot": 9000,
            "fecha_hora_inicio": datetime(2026, 7, 25, 10, 0),
            "estado": "ACTIVO",
        }

    @patch.object(operaciones_servicio_controller, "obtener_print_jobs_pc_activos", return_value=True)
    @patch.object(operaciones_servicio_controller, "asegurar_schema_operaciones_servicio")
    @patch.object(operaciones_servicio_controller, "db_cursor")
    def test_finalizar_cobrando_crea_un_job_durable(self, db_cursor, _ensure, _obtener_print_jobs_pc_activos):
        cursor = FakeCursor(self.operation)
        db_cursor.return_value = fake_db_cursor(cursor)

        result = operaciones_servicio_controller.finalizar_solo_lavado_cobrando(31, "cajero")

        db_cursor.assert_called_once_with(dictionary=True, commit=True)
        jobs = [params for query, params in cursor.executed if "INSERT INTO print_jobs" in query]
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0][:4], ("TICKET_SOLO_LAVADO", "PC_PDF", None, "ABC123"))
        self.assertEqual(jobs[0][5:], ("PENDIENTE", "desktop-solo-lavado:31:pc-pdf"))
        payload = json.loads(jobs[0][4])
        self.assertEqual(payload["kind"], "TICKET_SOLO_LAVADO")
        self.assertEqual(payload["servicio"], "SUV")
        self.assertEqual(payload["monto_final"], 9000)
        self.assertEqual(result["id_operacion_servicio"], 31)

    @patch.object(operaciones_servicio_controller, "obtener_print_jobs_pc_activos", return_value=True)
    @patch.object(operaciones_servicio_controller, "asegurar_schema_operaciones_servicio")
    def test_job_failure_rolls_back_service_finalization(self, _ensure, _obtener_print_jobs_pc_activos):
        connection = FakeConnection(FailingPrintJobCursor(self.operation))

        with patch.object(operaciones_servicio_controller, "db_cursor", db_utils.db_cursor), patch.object(
            db_utils, "get_connection", return_value=connection
        ):
            with self.assertRaisesRegex(RuntimeError, "print job unavailable"):
                operaciones_servicio_controller.finalizar_solo_lavado_cobrando(31, "cajero")

        self.assertFalse(connection.committed)
        self.assertTrue(connection.rolled_back)

    @patch.object(operaciones_servicio_controller, "asegurar_schema_operaciones_servicio")
    def test_finalizar_cobrando_confirma_y_crea_job_si_falla_la_lectura_de_configuracion(
        self, _ensure
    ):
        cursor = FailingConfigLookupCursor(self.operation)
        connection = FakeConnection(cursor)

        with patch.object(operaciones_servicio_controller, "db_cursor", db_utils.db_cursor), patch.object(
            db_utils, "get_connection", return_value=connection
        ):
            result = operaciones_servicio_controller.finalizar_solo_lavado_cobrando(31, "cajero")

        self.assertEqual(result["estado"], operaciones_servicio_controller.ESTADO_FINALIZADO_COBRADO)
        self.assertTrue(connection.committed)
        self.assertFalse(connection.rolled_back)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("UPDATE operaciones_servicio", consultas)
        self.assertIn("INSERT INTO print_jobs", consultas)

    @patch.object(operaciones_servicio_controller, "obtener_print_jobs_pc_activos", return_value=False)
    @patch.object(operaciones_servicio_controller, "asegurar_schema_operaciones_servicio")
    @patch.object(operaciones_servicio_controller, "db_cursor")
    def test_finalizar_cobrando_no_crea_job_cuando_la_impresion_pc_esta_desactivada(
        self, db_cursor, _ensure, _obtener_print_jobs_pc_activos
    ):
        cursor = FakeCursor(self.operation)
        db_cursor.return_value = fake_db_cursor(cursor)

        result = operaciones_servicio_controller.finalizar_solo_lavado_cobrando(31, "cajero")

        self.assertEqual(result["estado"], operaciones_servicio_controller.ESTADO_FINALIZADO_COBRADO)
        self.assertIn("UPDATE operaciones_servicio", "\n".join(query for query, _ in cursor.executed))
        self.assertNotIn("INSERT INTO print_jobs", "\n".join(query for query, _ in cursor.executed))

    def test_idempotency_key_is_stable(self):
        self.assertEqual(solo_lavado_idempotency_key(31), "desktop-solo-lavado:31:pc-pdf")
        self.assertEqual(solo_lavado_idempotency_key(31), solo_lavado_idempotency_key(31))


if __name__ == "__main__":
    unittest.main()
