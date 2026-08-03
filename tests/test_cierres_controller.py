import unittest
from unittest.mock import patch

from controllers import cierres_controller


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

    @patch.object(cierres_controller, "db_cursor")
    def test_rechaza_cierre_local_sin_acceder_a_base_de_datos(self, db_cursor):
        exito, mensaje = cierres_controller.realizar_cierre_diario("admin")

        self.assertFalse(exito)
        self.assertEqual(
            mensaje,
            "El cierre diario no está disponible en Desktop. Realícelo desde Mobile/API.",
        )
        db_cursor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
