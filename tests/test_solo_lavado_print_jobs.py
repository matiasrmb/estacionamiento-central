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

    @patch.object(operaciones_servicio_controller, "asegurar_schema_operaciones_servicio")
    @patch.object(operaciones_servicio_controller, "db_cursor")
    @patch.object(operaciones_servicio_controller, "generar_ticket_solo_lavado", create=True)
    def test_finalizar_cobrando_crea_un_job_durable_sin_ticket_local(self, local_ticket, db_cursor, _ensure):
        cursor = FakeCursor(self.operation)
        db_cursor.return_value = fake_db_cursor(cursor)

        result = operaciones_servicio_controller.finalizar_solo_lavado_cobrando(31, "cajero")

        db_cursor.assert_called_once_with(dictionary=True, commit=True)
        local_ticket.assert_not_called()
        jobs = [params for query, params in cursor.executed if "INSERT INTO print_jobs" in query]
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0][:4], ("TICKET_SOLO_LAVADO", "PC_PDF", None, "ABC123"))
        self.assertEqual(jobs[0][5:], ("PENDIENTE", "desktop-solo-lavado:31:pc-pdf"))
        payload = json.loads(jobs[0][4])
        self.assertEqual(payload["kind"], "TICKET_SOLO_LAVADO")
        self.assertEqual(payload["servicio"], "SUV")
        self.assertEqual(payload["monto_final"], 9000)
        self.assertEqual(result["id_operacion_servicio"], 31)

    @patch.object(operaciones_servicio_controller, "asegurar_schema_operaciones_servicio")
    def test_job_failure_rolls_back_service_finalization(self, _ensure):
        connection = FakeConnection(FailingPrintJobCursor(self.operation))

        with patch.object(operaciones_servicio_controller, "db_cursor", db_utils.db_cursor), patch.object(
            db_utils, "get_connection", return_value=connection
        ):
            with self.assertRaisesRegex(RuntimeError, "print job unavailable"):
                operaciones_servicio_controller.finalizar_solo_lavado_cobrando(31, "cajero")

        self.assertFalse(connection.committed)
        self.assertTrue(connection.rolled_back)

    def test_idempotency_key_is_stable(self):
        self.assertEqual(solo_lavado_idempotency_key(31), "desktop-solo-lavado:31:pc-pdf")
        self.assertEqual(solo_lavado_idempotency_key(31), solo_lavado_idempotency_key(31))


if __name__ == "__main__":
    unittest.main()
