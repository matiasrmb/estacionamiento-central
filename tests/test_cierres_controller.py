import unittest
from unittest.mock import patch

from controllers import cierres_controller
from utils.api_client import ApiClientError


class RealizarCierreDiarioTests(unittest.TestCase):
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
        self.assertIn("CREATE TABLE IF NOT EXISTS pagos_mensuales", schema)
        self.assertIn("UNIQUE KEY uq_pagos_mensuales_vehiculo_periodo", schema)
        self.assertIn("id_cierre INT NULL", schema)

    @patch.object(cierres_controller, "generar_pdf_cierre")
    @patch.object(cierres_controller, "crear_cierre_api")
    @patch.object(cierres_controller, "db_cursor")
    def test_cierre_exitoso_usa_api_y_generar_pdf_sin_acceder_a_base_de_datos(
        self, db_cursor, crear_cierre_api, generar_pdf
    ):
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
        db_cursor.assert_not_called()

    @patch.object(cierres_controller, "crear_cierre_api")
    @patch.object(cierres_controller, "db_cursor")
    def test_informa_conflicto_de_cierre_en_curso_sin_acceder_a_base_de_datos(self, db_cursor, crear_cierre_api):
        crear_cierre_api.side_effect = ApiClientError(409, "DAILY_CLOSE_IN_PROGRESS")

        exito, mensaje = cierres_controller.realizar_cierre_diario("token-api")

        self.assertFalse(exito)
        self.assertEqual(mensaje, "Hay otro cierre diario en curso. Intente nuevamente cuando finalice.")
        db_cursor.assert_not_called()

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

    @patch.object(cierres_controller, "db_cursor")
    def test_rechaza_cierre_sin_token_sin_acceder_a_base_de_datos(self, db_cursor):
        exito, mensaje = cierres_controller.realizar_cierre_diario(None)

        self.assertFalse(exito)
        self.assertEqual(mensaje, "No hay una sesión válida con la API. Inicie sesión nuevamente.")
        db_cursor.assert_not_called()

    @patch.object(cierres_controller, "db_cursor")
    def test_informa_advertencia_de_login_api_sin_acceder_a_base_de_datos(self, db_cursor):
        warning = "No fue posible iniciar sesión con la API al ingresar."

        exito, mensaje = cierres_controller.realizar_cierre_diario(None, warning)

        self.assertFalse(exito)
        self.assertEqual(mensaje, warning)
        db_cursor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
