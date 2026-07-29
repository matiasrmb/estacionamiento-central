import unittest
from unittest.mock import Mock, patch

from views.admin_edicion import EdicionIngresosWindow
from views.registro import QMessageBox, RegistroWindow


class RegistroViewReingresoTests(unittest.TestCase):
    def test_reingreso_no_solicita_motivo_y_lo_envia_como_opcional(self):
        vista = Mock()
        vista.input_patente.text.return_value = "abc123"
        vista.usuario = "operador"
        vista.validar_patente.return_value = (True, "")

        with patch("controllers.registro_controller.obtener_ingresos_editables") as obtener_ingresos, \
             patch("controllers.registro_controller.reingresar_vehiculo_cerrado") as reingresar, \
             patch("views.registro.QMessageBox.question", return_value=QMessageBox.Yes), \
             patch("views.registro.QMessageBox.information"), \
             patch("views.registro.QInputDialog.getText") as pedir_motivo:
            obtener_ingresos.return_value = [{
                "id_ingreso": 42,
                "patente": "ABC123",
                "estado": "CERRADO",
            }]
            reingresar.return_value = (True, "Salida revertida.")

            RegistroWindow.reingresar_vehiculo(vista)

        pedir_motivo.assert_not_called()
        reingresar.assert_called_once_with(42, "operador", True)
        vista.actualizar_tabla_activos.assert_called_once_with()


class EdicionIngresosViewReingresoTests(unittest.TestCase):
    def test_reingreso_no_solicita_motivo_y_lo_envia_como_opcional(self):
        vista = Mock()
        vista.usuario_admin = "administrador"
        vista.tabla.currentRow.return_value = 0
        vista.tabla.item.side_effect = [Mock(text=Mock(return_value="CERRADO")), Mock(text=Mock(return_value="42"))]

        with patch("views.admin_edicion.reingresar_vehiculo_cerrado") as reingresar, \
             patch("views.admin_edicion.QMessageBox.question", return_value=QMessageBox.Yes), \
             patch("views.admin_edicion.QMessageBox.information"), \
             patch("PySide6.QtWidgets.QInputDialog.getText") as pedir_motivo:
            reingresar.return_value = (True, "Salida revertida.")

            EdicionIngresosWindow.reingresar(vista)

        pedir_motivo.assert_not_called()
        reingresar.assert_called_once_with(42, "administrador", True)
        vista.cargar_datos.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
