import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

from utils.api_client import ApiClientError
from views.main_window import MainWindow


class _ViewStub(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def cargar_datos(self):
        pass

    def cargar_gastos(self):
        pass


class MainWindowLogoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_failed_api_logout_keeps_window_open_and_allows_retry(self):
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
            window = MainWindow("operador", "operador", api_token="desktop-token")

        with (
            patch("views.main_window.cerrar_sesion", side_effect=ApiClientError("API_UNAVAILABLE")) as logout,
            patch("views.main_window.QMessageBox.warning") as warning,
            patch.object(window, "close") as close,
        ):
            window.cerrar_sesion()
            window.cerrar_sesion()

        self.assertEqual(logout.call_count, 2)
        warning.assert_called()
        close.assert_not_called()
        window.close()

    def test_logout_shows_the_api_session_summary(self):
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
            window = MainWindow("operador", "operador", api_token="desktop-token")

        resumen = {
            "cantidad": 1,
            "total": 1200,
            "hora_inicio": "2026-08-09T09:00:00",
        }
        with (
            patch("views.main_window.cerrar_sesion", return_value={"resumen": resumen}),
            patch("views.main_window.QMessageBox.information") as information,
            patch.object(window, "close") as close,
        ):
            window.cerrar_sesion()

        information.assert_called_once_with(
            window,
            "Resumen de sesión",
            "Sesión: 09-08-2026 09:00 - ahora\n"
            "Vehículos cobrados: 1\n"
            "Total recaudado: $1200",
        )
        close.assert_called_once()
        window.close()


if __name__ == "__main__":
    unittest.main()
