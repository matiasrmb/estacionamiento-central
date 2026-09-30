import os
import unittest
from datetime import datetime
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from views.reportes import ReportesWindow


class ReportesViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _crear_vista(self, api_token=None):
        with patch("views.reportes.obtener_patentes_conocidas", return_value=[]), \
             patch("views.reportes.obtener_usuarios", return_value=[]):
            return ReportesWindow(api_token=api_token)

    @patch("views.reportes.QMessageBox.information")
    @patch("views.reportes.obtener_resumen_dashboard_reportes")
    @patch("views.reportes.obtener_reportes")
    def test_muestra_resumen_canonico_api_sin_romper_tabla_local(self, reportes, dashboard, _messagebox):
        reportes.return_value = {
            "items": [
                {
                    "categoria": "Vehículo",
                    "patente": "ABC123",
                    "fecha_hora_ingreso": datetime(2026, 1, 10, 9, 0),
                    "fecha_hora_salida": datetime(2026, 1, 10, 10, 0),
                    "minutos": 60,
                    "tarifa_aplicada": 2500,
                    "usuario": "admin",
                }
            ],
            "totals": {"total_movimientos": 1, "total_general": 2500, "total_gastos": 0, "total_neto": 2500},
        }
        dashboard.return_value = {
            "source": "api",
            "catalog_version": "1.3.0",
            "period": {"id": "current", "state": "open"},
            "summary": [
                {"metric": "operational_income_total", "label": "Income", "value": 3000},
                {"metric": "operational_expense_total", "label": "Expenses", "value": 500},
                {"metric": "operational_net_total", "label": "Net", "value": 2500},
            ],
        }
        vista = self._crear_vista(api_token="desktop-token")

        vista.filtrar()

        self.assertIn("Fuente: API reporting", vista.label_dashboard_estado.text())
        self.assertIn("Versión catálogo: 1.3.0", vista.label_dashboard_estado.text())
        self.assertEqual([card.label_valor.text() for card in vista.dashboard_metric_cards[:3]], ["$3000", "$500", "$2500"])
        self.assertEqual(vista.tabla.rowCount(), 2)
        self.assertTrue(vista.boton_exportar.isEnabled())
        dashboard.assert_called_once()
        self.assertEqual(dashboard.call_args.kwargs["token"], "desktop-token")
        vista.close()

    @patch("views.reportes.QMessageBox.information")
    @patch("views.reportes.obtener_resumen_dashboard_reportes")
    @patch("views.reportes.obtener_reportes")
    def test_sin_token_muestra_resumen_local_y_no_rompe_pantalla(self, reportes, dashboard, _messagebox):
        reportes.return_value = {
            "items": [],
            "totals": {"total_movimientos": 0, "total_general": 0, "total_gastos": 0, "total_neto": 0},
        }
        dashboard.return_value = reportes.return_value
        vista = self._crear_vista()

        vista.filtrar()

        self.assertIn("Sin sesión API", vista.label_dashboard_estado.text())
        self.assertEqual([card.label_valor.text() for card in vista.dashboard_metric_cards[:3]], ["$0", "$0", "$0"])
        self.assertEqual(vista.tabla.rowCount(), 0)
        self.assertFalse(vista.boton_exportar.isEnabled())
        dashboard.assert_called_once()
        self.assertIsNone(dashboard.call_args.kwargs["token"])
        vista.close()


if __name__ == "__main__":
    unittest.main()
