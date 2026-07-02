import unittest
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import patch

from controllers import operaciones_servicio_controller as solo_controller


class FakeCursor:
    def __init__(self, fetchone_results=None):
        self.fetchone_results = list(fetchone_results or [])
        self.executed = []
        self.lastrowid = 44
        self.rowcount = 1

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        if self.fetchone_results:
            return self.fetchone_results.pop(0)
        return None


@contextmanager
def fake_db_cursor(cursor):
    yield cursor


class SoloLavadoDesktopControllerTests(unittest.TestCase):
    @patch.object(solo_controller, "datetime")
    @patch.object(solo_controller, "db_cursor")
    def test_iniciar_solo_lavado_usa_tipo_activo_y_snapshot_de_precio(self, db_cursor, datetime_mock):
        ahora = datetime(2026, 7, 1, 10, 0)
        datetime_mock.now.return_value = ahora
        cursor = FakeCursor(fetchone_results=[
            None,
            {"id_tipo_vehiculo_lavado": 7, "nombre": "SUV", "valor_lavado": 9000, "activo": 1},
        ])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = solo_controller.iniciar_solo_lavado("aa111aa", 7, "operador")

        self.assertEqual(resultado["id_operacion_servicio"], 44)
        self.assertEqual(resultado["patente"], "AA111AA")
        self.assertEqual(resultado["tipo_vehiculo_lavado_snapshot"], "SUV")
        self.assertEqual(resultado["valor_lavado_snapshot"], 9000)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("FROM ingresos i", consultas)
        self.assertIn("FROM tipos_vehiculo_lavado", consultas)
        self.assertIn("INSERT INTO operaciones_servicio", consultas)

    @patch.object(solo_controller, "db_cursor")
    def test_iniciar_solo_lavado_rechaza_patente_con_ingreso_activo(self, db_cursor):
        cursor = FakeCursor(fetchone_results=[{"id_ingreso": 10}])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = solo_controller.iniciar_solo_lavado("AA111AA", 7, "operador")

        self.assertIsNone(resultado)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertNotIn("INSERT INTO operaciones_servicio", consultas)

    @patch.object(solo_controller, "generar_ticket_solo_lavado")
    @patch.object(solo_controller, "datetime")
    @patch.object(solo_controller, "db_cursor")
    def test_finalizar_solo_lavado_cobrando_genera_ticket_y_no_crea_ingreso(
        self,
        db_cursor,
        datetime_mock,
        generar_ticket,
    ):
        inicio = datetime(2026, 7, 1, 10, 0)
        fin = datetime(2026, 7, 1, 10, 30)
        datetime_mock.now.return_value = fin
        operacion = {
            "id_operacion_servicio": 44,
            "patente": "AA111AA",
            "id_tipo_vehiculo_lavado": 7,
            "tipo_vehiculo_lavado_snapshot": "SUV",
            "valor_lavado_snapshot": 9000,
            "fecha_hora_inicio": inicio,
            "estado": "ACTIVO",
        }
        cursor = FakeCursor(fetchone_results=[operacion])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = solo_controller.finalizar_solo_lavado_cobrando(44, "cajero")

        self.assertEqual(resultado["estado"], solo_controller.ESTADO_FINALIZADO_COBRADO)
        self.assertEqual(resultado["duracion_minutos"], 30)
        self.assertEqual(resultado["valor_lavado_snapshot"], 9000)
        generar_ticket.assert_called_once()
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("UPDATE operaciones_servicio", consultas)
        self.assertNotIn("INSERT INTO ingresos", consultas)

    @patch.object(solo_controller, "datetime")
    @patch.object(solo_controller, "db_cursor")
    def test_finalizar_solo_lavado_como_estadia_crea_ingreso_desde_fin_y_difiere_cobro(
        self,
        db_cursor,
        datetime_mock,
    ):
        inicio = datetime(2026, 7, 1, 10, 0)
        fin = datetime(2026, 7, 1, 10, 45)
        datetime_mock.now.return_value = fin
        operacion = {
            "id_operacion_servicio": 45,
            "patente": "BB222BB",
            "id_tipo_vehiculo_lavado": 8,
            "tipo_vehiculo_lavado_snapshot": "Camioneta",
            "valor_lavado_snapshot": 10000,
            "fecha_hora_inicio": inicio,
            "estado": "ACTIVO",
        }
        cursor = FakeCursor(fetchone_results=[operacion, None])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = solo_controller.finalizar_solo_lavado_como_estadia(45, "operador")

        self.assertEqual(resultado["estado"], solo_controller.ESTADO_CONVERTIDO_ESTADIA)
        self.assertEqual(resultado["fecha_hora_fin"], fin)
        self.assertEqual(resultado["fecha_hora_ingreso"], fin)
        self.assertEqual(resultado["id_ingreso_generado"], 44)
        self.assertFalse(resultado["cobra_ahora"])
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("INSERT INTO vehiculos", consultas)
        self.assertIn("INSERT INTO ingresos", consultas)
        self.assertIn("id_ingreso_generado", consultas)


if __name__ == "__main__":
    unittest.main()
