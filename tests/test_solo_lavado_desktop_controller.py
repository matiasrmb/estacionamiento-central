import unittest
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
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
    def setUp(self):
        solo_controller._SCHEMA_ENSURED = False

    @patch.object(solo_controller, "db_cursor")
    def test_asegurar_schema_operaciones_servicio_crea_tabla_y_columnas(self, db_cursor):
        cursor = FakeCursor()
        db_cursor.return_value = fake_db_cursor(cursor)

        solo_controller.asegurar_schema_operaciones_servicio()

        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("CREATE TABLE IF NOT EXISTS operaciones_servicio", consultas)
        self.assertIn("cerrado TINYINT(1) NOT NULL DEFAULT 0", consultas)
        self.assertIn("ALTER TABLE cierres_diarios ADD COLUMN total_lavados_solos", consultas)

    @patch.object(solo_controller, "db_cursor")
    def test_asegurar_schema_operaciones_servicio_oculta_error_crudo(self, db_cursor):
        db_cursor.side_effect = RuntimeError("raw db failure")

        with self.assertRaises(RuntimeError) as raised:
            solo_controller.asegurar_schema_operaciones_servicio()

        self.assertEqual(str(raised.exception), solo_controller.SOLO_LAVADO_SCHEMA_ERROR_MESSAGE)
        self.assertFalse(solo_controller._SCHEMA_ENSURED)

    def test_registro_view_catches_solo_lavado_runtime_errors(self):
        source = Path(__file__).resolve().parents[1].joinpath("views", "registro.py").read_text(encoding="utf-8")

        self.assertIn("except RuntimeError as exc:", source)
        self.assertIn("obtener_solo_lavados_activos()", source)
        self.assertIn("QMessageBox.critical(self, \"Solo lavado no disponible\", str(exc))", source)

    def test_registro_view_uses_actionable_message_when_no_active_solo_lavado_types(self):
        source = Path(__file__).resolve().parents[1].joinpath("views", "registro.py").read_text(encoding="utf-8")

        self.assertIn("SOLO_LAVADO_PRICE_CONFIG_MESSAGE", source)
        self.assertIn("QMessageBox.warning(self, \"Sin tipos activos\", SOLO_LAVADO_PRICE_CONFIG_MESSAGE)", source)

    @patch.object(solo_controller, "asegurar_schema_operaciones_servicio")
    def test_obtener_solo_lavados_activos_propaga_mensaje_claro_de_schema(self, ensure):
        ensure.side_effect = RuntimeError(solo_controller.SOLO_LAVADO_SCHEMA_ERROR_MESSAGE)

        with self.assertRaises(RuntimeError) as raised:
            solo_controller.obtener_solo_lavados_activos()

        self.assertEqual(str(raised.exception), solo_controller.SOLO_LAVADO_SCHEMA_ERROR_MESSAGE)

    @patch.object(solo_controller, "datetime")
    @patch.object(solo_controller, "asegurar_schema_operaciones_servicio")
    @patch.object(solo_controller, "db_cursor")
    def test_iniciar_solo_lavado_usa_tipo_activo_y_snapshot_de_precio(self, db_cursor, _ensure, datetime_mock):
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
        self.assertFalse(any(
            ("CREATE" in query.upper() or "ALTER" in query.upper())
            and "TIPOS_VEHICULO_LAVADO" in query.upper()
            for query, _ in cursor.executed
        ))

    @patch.object(solo_controller, "asegurar_schema_operaciones_servicio")
    @patch.object(solo_controller, "db_cursor")
    def test_iniciar_solo_lavado_rechaza_patente_con_ingreso_activo(self, db_cursor, _ensure):
        cursor = FakeCursor(fetchone_results=[{"id_ingreso": 10}])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = solo_controller.iniciar_solo_lavado("AA111AA", 7, "operador")

        self.assertIsNone(resultado)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertNotIn("INSERT INTO operaciones_servicio", consultas)

    @patch.object(solo_controller, "datetime")
    @patch.object(solo_controller, "asegurar_schema_operaciones_servicio")
    @patch.object(solo_controller, "db_cursor")
    def test_iniciar_solo_lavado_permite_patente_con_solo_ingreso_anulado(
        self,
        db_cursor,
        _ensure,
        datetime_mock,
    ):
        ahora = datetime(2026, 7, 1, 10, 0)
        datetime_mock.now.return_value = ahora
        cursor = FakeCursor(fetchone_results=[
            None,
            {"id_tipo_vehiculo_lavado": 7, "nombre": "SUV", "valor_lavado": 9000, "activo": 1},
        ])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = solo_controller.iniciar_solo_lavado("AA111AA", 7, "operador")

        self.assertEqual(resultado["id_operacion_servicio"], 44)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("FROM ingresos_eliminados ie", consultas)
        self.assertIn("ie.id_ingreso_original = i.id_ingreso", consultas)
        self.assertIn("INSERT INTO operaciones_servicio", consultas)

    @patch.object(solo_controller, "asegurar_schema_operaciones_servicio")
    @patch.object(solo_controller, "db_cursor")
    def test_iniciar_solo_lavado_rechaza_patente_con_ingreso_en_espera(self, db_cursor, _ensure):
        cursor = FakeCursor(fetchone_results=[{"id_ingreso": 11}])
        db_cursor.return_value = fake_db_cursor(cursor)

        resultado = solo_controller.iniciar_solo_lavado("AA111AA", 7, "operador")

        self.assertIsNone(resultado)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertNotIn("en_espera = 0", consultas)
        self.assertNotIn("INSERT INTO operaciones_servicio", consultas)

    @patch.object(solo_controller, "datetime")
    @patch.object(solo_controller, "asegurar_schema_operaciones_servicio")
    @patch.object(solo_controller, "db_cursor")
    def test_finalizar_solo_lavado_cobrando_crea_job_durable_y_no_crea_ingreso(
        self,
        db_cursor,
        _ensure,
        datetime_mock,
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
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("UPDATE operaciones_servicio", consultas)
        self.assertIn("INSERT INTO print_jobs", consultas)
        self.assertNotIn("INSERT INTO ingresos", consultas)

    @patch.object(solo_controller, "datetime")
    @patch.object(solo_controller, "asegurar_schema_operaciones_servicio")
    @patch.object(solo_controller, "db_cursor")
    def test_finalizar_solo_lavado_como_estadia_crea_ingreso_desde_fin_y_difiere_cobro(
        self,
        db_cursor,
        _ensure,
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
