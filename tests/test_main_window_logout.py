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
            patch("views.main_window.obtener_resumen_sesion", side_effect=ApiClientError("API_UNAVAILABLE")) as summary,
            patch("views.main_window.QMessageBox.warning") as warning,
            patch.object(window, "close") as close,
        ):
            window.cerrar_sesion()
            window.cerrar_sesion()

        self.assertEqual(summary.call_count, 2)
        warning.assert_called()
        close.assert_not_called()
        window.close()

    def test_logout_confirms_with_pre_summary_then_shows_final_net_amount(self):
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
            "hora_inicio": "2026-08-09T09:00:00",
            "hora_cierre": "2026-08-09T10:00:00",
            "ingresos": {"cantidad": 1, "total": 1200},
            "usos_bano": {"cantidad": 0, "total": 0},
            "lavados": {"cantidad": 0, "total": 0},
            "mensualidades": {"cantidad": 0, "total": 0},
            "noches": {"cantidad": 0, "total": 0},
            "total_ingresos": 1200,
            "gastos_asociados": 200,
            "neto_caja": 1000,
        }
        with (
            patch("views.main_window.obtener_resumen_sesion", return_value={"resumen": resumen}) as pre_summary,
            patch("views.main_window.QMessageBox.question", return_value=QMessageBox.Yes) as question,
            patch("views.main_window.cerrar_sesion", return_value={"resumen": resumen}),
            patch("views.main_window.QMessageBox.information") as information,
            patch.object(window, "close") as close,
        ):
            window.cerrar_sesion()

        pre_summary.assert_called_once_with("desktop-token")
        self.assertIn("Gastos asociados: -$200", question.call_args.args[2])
        self.assertNotIn("Lavados cobrados", question.call_args.args[2])
        information.assert_called_once_with(
            window,
            "Resumen de sesión",
            "Inicio de sesión: 09-08-2026 09:00\n"
            "Cierre de sesión: 09-08-2026 10:00\n"
            "Neto de la sesión: $1000",
        )
        close.assert_called_once()
        window.close()

    def test_cancelled_logout_does_not_close_the_api_session(self):
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
            patch("views.main_window.obtener_resumen_sesion", return_value={"resumen": {}}),
            patch("views.main_window.QMessageBox.question", return_value=QMessageBox.No),
            patch("views.main_window.cerrar_sesion") as logout,
            patch.object(window, "close") as close,
        ):
            window.cerrar_sesion()

        logout.assert_not_called()
        close.assert_not_called()
        window.close()

    def test_logout_without_api_session_does_not_show_a_zero_summary(self):
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

        with (
            patch("views.main_window.QMessageBox.warning") as warning,
            patch.object(window, "close") as close,
        ):
            window.cerrar_sesion()

        warning.assert_called_once()
        close.assert_not_called()
        window.close()


if __name__ == "__main__":
    unittest.main()
