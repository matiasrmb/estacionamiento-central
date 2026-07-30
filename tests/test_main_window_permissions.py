import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QWidget
from views.main_window import MainWindow


class _ViewStub(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def cargar_datos(self):
        pass

    def cargar_gastos(self):
        pass


class MainWindowPermissionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_operador_ve_y_navega_a_mensuales_y_gastos_sin_acceso_a_modulos_administrativos(self):
        with (
            patch("views.main_window.DashboardWindow", _ViewStub),
            patch("views.main_window.RegistroWindow", _ViewStub),
            patch("views.main_window.ReportesWindow", _ViewStub),
            patch("views.main_window.MensualesWindow", _ViewStub),
            patch("views.main_window.ConfiguracionWindow", _ViewStub),
            patch("views.main_window.TarifasPersonalizadasWindow", _ViewStub),
            patch("views.main_window.EdicionIngresosWindow", _ViewStub),
            patch("views.main_window.UsuariosWindow", _ViewStub),
            patch("views.main_window.AsistenciasWindow", _ViewStub),
            patch("views.main_window.GastosWindow", _ViewStub),
        ):
            window = MainWindow("operador", "operador")

        sidebar_labels = [text for _, text, _ in window.sidebar_buttons_data]
        self.assertIn("Gastos operacionales", sidebar_labels)
        self.assertIn("Clientes mensuales", sidebar_labels)
        self.assertNotIn("Reportes", sidebar_labels)
        self.assertNotIn("Configuración", sidebar_labels)
        self.assertNotIn("Tarifas personalizadas", sidebar_labels)
        self.assertNotIn("Edición de ingresos", sidebar_labels)
        self.assertNotIn("Gestión de usuarios", sidebar_labels)
        self.assertNotIn("Asistencias", sidebar_labels)

        window.btn_mensuales.click()
        self.assertEqual(window.label_modulo.text(), "Clientes mensuales")
        self.assertIs(window.stack.currentWidget(), window.mensuales_page)

        with patch.object(window.gastos_view, "cargar_gastos") as cargar_gastos:
            window.btn_gastos.click()

        self.assertEqual(window.label_modulo.text(), "Gastos operacionales")
        self.assertIs(window.stack.currentWidget(), window.gastos_page)
        cargar_gastos.assert_called_once_with()
        window.close()


if __name__ == "__main__":
    unittest.main()
