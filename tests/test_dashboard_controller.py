import unittest
from unittest.mock import patch

from controllers import dashboard_controller


class FakeCursor:
    def __init__(self, fetchone_results):
        self.fetchone_results = list(fetchone_results)
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self.fetchone_results.pop(0)


class FakeDbCursorContext:
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc, traceback):
        return False


class DashboardControllerTests(unittest.TestCase):
    def test_calcular_metricas_panel_separa_caja_de_proyecciones(self):
        caja = {
            "total_banos": 2,
            "total_banos_monto": 600,
            "total_lavados_solos": 1,
            "total_lavados_solos_monto": 8000,
            "total_noches": 1,
            "total_noches_monto": 5000,
            "total_general": 14600,
            "total_gastos": 1600,
            "total_neto": 13000,
        }
        metricas = dashboard_controller.calcular_metricas_panel(
            caja,
            [{"monto": 2500}, {"monto": 0}],
            [{"valor_lavado_snapshot": 4000, "id_ingreso_generado": None}],
            {"cantidad": 3, "monto": 150000},
        )

        self.assertEqual(metricas["vehiculos_activos"], 2)
        self.assertEqual(metricas["estimado_por_cobrar"], 6500)
        self.assertEqual(metricas["total_proyectado"], 21100)
        self.assertEqual(metricas["noches_cobradas_monto"], 5000)
        self.assertEqual(metricas["gastos"], 1600)

    @patch.object(dashboard_controller, "obtener_solo_lavados_activos", return_value=[])
    @patch.object(dashboard_controller, "obtener_vehiculos_activos", return_value=[])
    @patch.object(dashboard_controller, "obtener_resumen_caja_actual")
    @patch.object(dashboard_controller, "db_cursor")
    def test_resumen_usa_pagos_mensuales_del_mes_y_excluye_ingresos_eliminados(
        self, db_cursor, obtener_caja, _vehiculos, _lavados
    ):
        cursor = FakeCursor([
            {"ultima_cierre": None},
            {"total": 7},
            {"cantidad": 2, "monto": 80000},
        ])
        db_cursor.return_value = FakeDbCursorContext(cursor)
        obtener_caja.return_value = {
            "total_banos": 0,
            "total_banos_monto": 0,
            "total_lavados_solos": 0,
            "total_lavados_solos_monto": 0,
            "total_noches": 0,
            "total_noches_monto": 0,
            "total_general": 0,
            "total_gastos": 0,
            "total_neto": 0,
        }

        resumen = dashboard_controller.obtener_resumen_diario()

        self.assertEqual(resumen["total_ingresos"], 7)
        self.assertEqual(resumen["mensualidades_mes"], 2)
        self.assertEqual(resumen["mensualidades_mes_monto"], 80000)
        consultas = "\n".join(query for query, _ in cursor.executed)
        self.assertIn("FROM ingresos_eliminados", consultas)
        self.assertIn("fecha_pago >= DATE_FORMAT(CURDATE(), '%Y-%m-01')", consultas)


if __name__ == "__main__":
    unittest.main()
