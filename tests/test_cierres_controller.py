import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from controllers import cierres_controller
from controllers import operaciones_servicio_controller
from utils.api_client import ApiClientError


class FakeCursor:
    def __init__(self, fetchone_results=None, fetchall_results=None, lastrowid=77):
        self.fetchone_results = list(fetchone_results or [])
        self.fetchall_results = list(fetchall_results or [])
        self.lastrowid = lastrowid
        self.rowcount = 0
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))
        if query.lstrip().upper().startswith("UPDATE"):
            self.rowcount = len(params[0]) if params and isinstance(params[0], (list, tuple)) else 1

    def fetchone(self):
        return self.fetchone_results.pop(0) if self.fetchone_results else None

    def fetchall(self):
        return self.fetchall_results.pop(0) if self.fetchall_results else []


@contextmanager
def fake_db_cursor(cursor):
    yield cursor


class RealizarCierreDiarioTests(unittest.TestCase):
    def test_cierre_no_repara_schema_en_runtime(self):
        source = Path("controllers/cierres_controller.py").read_text(encoding="utf-8")

        self.assertNotIn("asegurar_schema_cierres", source)
        self.assertNotIn("CREATE TABLE", source)
        self.assertNotIn("ALTER TABLE cierres_diarios", source)
        self.assertNotIn("ALTER TABLE usos_bano", source)

    def test_schema_declara_vinculos_y_totales_canonicos_de_cierre(self):
        with open("schema.sql", encoding="utf-8") as schema_file:
            schema = schema_file.read()

        self.assertIn("CREATE TABLE IF NOT EXISTS gastos_operacion", schema)
        self.assertIn("total_gastos INT NOT NULL DEFAULT 0", schema)
        self.assertIn("total_neto INT NOT NULL DEFAULT 0", schema)
        self.assertIn("total_mensualidades INT NOT NULL DEFAULT 0", schema)
        self.assertIn("total_mensualidades_monto INT NOT NULL DEFAULT 0", schema)
        self.assertIn("total_noches INT NOT NULL DEFAULT 0", schema)
        self.assertIn("total_noches_monto INT NOT NULL DEFAULT 0", schema)
        self.assertIn("total_lavados_solos_monto INT NOT NULL DEFAULT 0", schema)
        self.assertIn("id_cierre INT NULL", schema)
        self.assertIn("idx_operaciones_servicio_id_cierre", schema)
        self.assertIn("FOREIGN KEY (id_cierre) REFERENCES cierres_diarios(id_cierre)", schema)
        self.assertIn("CREATE TABLE IF NOT EXISTS pagos_mensuales", schema)
        self.assertIn("UNIQUE KEY uq_pagos_mensuales_vehiculo_periodo", schema)
        self.assertIn("id_cierre INT NULL", schema)

    def test_asegura_schema_operaciones_servicio_cierre_agrega_soporte_faltante(self):
        cursor = FakeCursor(fetchall_results=[
            [{"Field": "cerrado"}],
            [{"Key_name": "idx_operaciones_servicio_cierre"}],
        ])

        operaciones_servicio_controller.asegurar_schema_operaciones_servicio_cierre(cursor)

        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("SHOW COLUMNS FROM operaciones_servicio", consultas)
        self.assertIn("ALTER TABLE operaciones_servicio ADD COLUMN id_cierre INT NULL", consultas)
        self.assertIn("CREATE INDEX idx_operaciones_servicio_id_cierre", consultas)

    def test_asegura_schema_operaciones_servicio_cierre_es_idempotente(self):
        cursor = FakeCursor(fetchall_results=[
            [{"Field": "cerrado"}, {"Field": "id_cierre"}],
            [{"Key_name": "idx_operaciones_servicio_cierre"}, {"Key_name": "idx_operaciones_servicio_id_cierre"}],
        ])

        operaciones_servicio_controller.asegurar_schema_operaciones_servicio_cierre(cursor)

        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("SHOW COLUMNS FROM operaciones_servicio", consultas)
        self.assertNotIn("ALTER TABLE operaciones_servicio ADD COLUMN id_cierre", consultas)
        self.assertNotIn("CREATE INDEX idx_operaciones_servicio_id_cierre", consultas)

    def test_cierre_exitoso_incluye_y_marca_lavado_solo_cobrado_una_vez(self):
        cursor = FakeCursor(
            fetchall_results=[
                [{"Field": "cerrado"}, {"Field": "id_cierre"}],
                [{"Key_name": "idx_operaciones_servicio_id_cierre"}],
                [{
                    "id_operacion_servicio": 11,
                    "estado": "FINALIZADO_COBRADO",
                    "valor_lavado_snapshot": 8000,
                    "cerrado": False,
                    "id_ingreso_generado": None,
                }],
            ],
            lastrowid=91,
        )
        cierre_api = {
            "fecha_inicio": "2026-08-03T08:00:00",
            "fecha_cierre": "2026-08-03T20:00:00",
            "total_recaudado": 1000,
            "total_banos": 0,
            "total_banos_monto": 0,
            "total_gastos": 0,
            "total_neto": 1000,
            "usuario": "admin",
        }

        with patch.object(cierres_controller, "db_cursor", return_value=fake_db_cursor(cursor)), \
             patch.object(cierres_controller, "crear_cierre_api", return_value=cierre_api), \
             patch.object(cierres_controller, "generar_pdf_cierre") as generar_pdf:
            exito, mensaje = cierres_controller.realizar_cierre_diario("token-api")

        self.assertTrue(exito)
        self.assertIn("$9000", mensaje)
        datos_pdf = generar_pdf.call_args.args[1]
        self.assertEqual(datos_pdf["Total recaudado lavados solos"], "$8000")
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("INSERT INTO cierres_diarios", consultas)
        self.assertIn("UPDATE operaciones_servicio", consultas)
        self.assertEqual(cursor.executed[-1][1], (91, (11,)))

    def test_cierre_fallido_en_api_no_marca_lavados_solos(self):
        cursor = FakeCursor()

        with patch.object(cierres_controller, "db_cursor", return_value=fake_db_cursor(cursor)), \
             patch.object(cierres_controller, "crear_cierre_api", side_effect=ApiClientError(409, "NO_PENDING_CLOSURE")):
            exito, mensaje = cierres_controller.realizar_cierre_diario("token-api")

        self.assertFalse(exito)
        self.assertEqual(mensaje, "No hay registros pendientes para cerrar.")
        self.assertEqual(cursor.executed, [])

    @patch.object(cierres_controller, "generar_pdf_cierre")
    @patch.object(cierres_controller, "crear_cierre_api")
    def test_cierre_exitoso_usa_api_y_generar_pdf(self, crear_cierre_api, generar_pdf):
        crear_cierre_api.return_value = {
            "fecha_inicio": "2026-08-03T08:00:00",
            "fecha_cierre": "2026-08-03T20:00:00",
            "total_recaudado": 1000,
            "total_banos": 1,
            "total_banos_monto": 300,
            "total_general": 1300,
            "total_gastos": 200,
            "total_neto": 1100,
            "usuario": "admin",
        }

        exito, mensaje = cierres_controller.realizar_cierre_diario("token-api")

        self.assertTrue(exito)
        self.assertIn("$1100", mensaje)
        crear_cierre_api.assert_called_once_with("token-api")
        generar_pdf.assert_called_once()
        self.assertEqual(generar_pdf.call_args.args[1]["Total neto del día"], "$1100")

    @patch.object(cierres_controller, "crear_cierre_api")
    def test_informa_conflicto_de_cierre_en_curso(self, crear_cierre_api):
        crear_cierre_api.side_effect = ApiClientError(409, "DAILY_CLOSE_IN_PROGRESS")

        exito, mensaje = cierres_controller.realizar_cierre_diario("token-api")

        self.assertFalse(exito)
        self.assertEqual(mensaje, "Hay otro cierre diario en curso. Intente nuevamente cuando finalice.")

    @patch.object(cierres_controller, "crear_cierre_api")
    def test_informa_sesion_api_invalida(self, crear_cierre_api):
        crear_cierre_api.side_effect = ApiClientError(401, "Invalid or expired token")

        exito, mensaje = cierres_controller.realizar_cierre_diario("token-vencido")

        self.assertFalse(exito)
        self.assertEqual(mensaje, "La sesión con la API no es válida o venció. Inicie sesión nuevamente.")

    @patch.object(cierres_controller, "crear_cierre_api")
    def test_informa_api_no_disponible(self, crear_cierre_api):
        crear_cierre_api.side_effect = ApiClientError(detail="API_UNAVAILABLE")

        exito, mensaje = cierres_controller.realizar_cierre_diario("token-api")

        self.assertFalse(exito)
        self.assertEqual(
            mensaje,
            "No se pudo conectar con la API. Verifique que el servicio esté disponible e inténtelo nuevamente.",
        )

    def test_rechaza_cierre_sin_token(self):
        exito, mensaje = cierres_controller.realizar_cierre_diario(None)

        self.assertFalse(exito)
        self.assertEqual(mensaje, "No hay una sesión válida con la API. Inicie sesión nuevamente.")

    def test_informa_advertencia_de_login_api(self):
        warning = "No fue posible iniciar sesión con la API al ingresar."

        exito, mensaje = cierres_controller.realizar_cierre_diario(None, warning)

        self.assertFalse(exito)
        self.assertEqual(mensaje, warning)


if __name__ == "__main__":
    unittest.main()
