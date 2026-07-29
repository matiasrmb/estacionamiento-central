import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from views.configuracion import ConfiguracionWindow


class ConfiguracionViewTests(unittest.TestCase):
    def test_toggle_de_trabajos_pc_esta_en_configuracion_general_visible(self):
        source = Path(__file__).resolve().parents[1].joinpath(
            "views", "configuracion.py"
        ).read_text(encoding="utf-8")

        checkbox = "layout_general.addWidget(self.print_jobs_pc_activos_check, 5, 0, 1, 2)"
        label = "layout_general.addWidget(self.print_jobs_pc_activos_label, 6, 0, 1, 2)"

        self.assertIn(checkbox, source)
        self.assertIn(label, source)
        self.assertNotIn("layout_impresion.addWidget(self.print_jobs_pc_activos_check", source)

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
