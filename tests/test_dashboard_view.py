import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from views.dashboard import DASHBOARD_METRICAS, DashboardWindow
from views.registro import TarjetaResumen


class DashboardViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @patch("views.dashboard.obtener_modo_privacidad_metricas", return_value=True)
    @patch("views.dashboard.DashboardWindow.actualizar_resumen")
    @patch("views.dashboard.DashboardWindow.obtener_periodo_resumen", return_value="Período del turno")
    def test_panel_agrupa_las_once_tarjetas_y_respeta_privacidad(self, _periodo, _resumen, _privacidad):
        vista = DashboardWindow("operador", "operador")

        self.assertEqual([seccion for seccion, _ in DASHBOARD_METRICAS], ["Operación", "Caja", "Proyección"])
        self.assertEqual(list(vista.tarjetas_metricas), [
            "ingresos", "vehiculos", "banos", "lavados", "mensualidades", "noches",
            "total_turno", "gastos", "neto_caja", "estimado", "total_proyectado",
        ])
        self.assertTrue(all(isinstance(tarjeta, TarjetaResumen) for tarjeta in vista.tarjetas_metricas.values()))
        self.assertTrue(vista.tarjetas_metricas["total_proyectado"].label_valor.isHidden())
        self.assertTrue(all(tarjeta.height() == 112 for tarjeta in vista.tarjetas_metricas.values()))
        vista.close()


if __name__ == "__main__":
    unittest.main()
