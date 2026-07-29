import unittest
import os
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from views.configuracion import ConfiguracionWindow


class ConfiguracionViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @patch("views.configuracion.listar_trabajos_impresion_impresos", return_value=[])
    @patch("views.configuracion.listar_trabajos_impresion_fallidos", return_value=[])
    @patch("views.configuracion.obtener_impresoras_instaladas", return_value=[])
    @patch("views.configuracion.obtener_configuracion", return_value={"pc_print_jobs_activos": "1"})
    def test_toggle_de_trabajos_pc_esta_visible_en_el_inicio_de_configuracion(
        self,
        _obtener_configuracion,
        _obtener_impresoras,
        _trabajos_fallidos,
        _trabajos_impresos,
    ):
        vista = ConfiguracionWindow()
        vista.show()
        self.app.processEvents()

        checkbox = vista.print_jobs_pc_activos_check
        self.assertTrue(checkbox.isVisible())
        self.assertEqual(checkbox.parentWidget().objectName(), "PanelImpresionPC")
        self.assertLess(
            vista.layout().indexOf(checkbox.parentWidget()),
            vista.layout().indexOf(vista.modo_combo.parentWidget()),
        )
        vista.close()

    @patch("views.configuracion.QMessageBox.information")
    @patch("views.configuracion.actualizar_configuracion")
    def test_guardar_persiste_el_toggle_de_trabajos_pc(self, actualizar_configuracion, _informacion):
        vista = SimpleNamespace(
            modo_combo=Mock(currentText=Mock(return_value="minuto")),
            minima_input=Mock(text=Mock(return_value="300")),
            minuto_input=Mock(text=Mock(return_value="25")),
            hora_input=Mock(text=Mock(return_value="1300")),
            bano_input=Mock(text=Mock(return_value="300")),
            lavado_inputs={},
            dias_limpieza_input=Mock(text=Mock(return_value="30")),
            limpieza_activa_check=Mock(isChecked=Mock(return_value=True)),
            print_jobs_pc_activos_check=Mock(isChecked=Mock(return_value=False)),
        )

        ConfiguracionWindow.guardar(vista)

        actualizar_configuracion.assert_any_call("pc_print_jobs_activos", 0)

    @patch("views.configuracion.QMessageBox.information")
    @patch("views.configuracion.obtener_configuracion", return_value={"pc_print_jobs_activos": "0"})
    def test_recargar_configuracion_restaura_el_toggle_de_trabajos_pc(self, _obtener_configuracion, _informacion):
        vista = SimpleNamespace(
            modo_combo=Mock(),
            minima_input=Mock(),
            minuto_input=Mock(),
            hora_input=Mock(),
            bano_input=Mock(),
            lavado_inputs={},
            limpieza_activa_check=Mock(),
            dias_limpieza_input=Mock(),
            print_jobs_pc_activos_check=Mock(),
            cargar_impresoras_en_combo=Mock(),
            actualizar_trabajos_impresion_fallidos=Mock(),
            actualizar_trabajos_impresion_impresos=Mock(),
        )

        ConfiguracionWindow.recargar_configuracion(vista)

        vista.print_jobs_pc_activos_check.setChecked.assert_called_once_with(False)


if __name__ == "__main__":
    unittest.main()
