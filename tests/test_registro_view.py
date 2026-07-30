import os
import unittest
from datetime import datetime
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QLineEdit
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


class RegistroViewF4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_f4_conserva_el_ciclo_despues_de_seleccionar_una_patente(self):
        vista = Mock()
        vista.busqueda_f4 = "AB"
        vista.patentes_f4 = []
        vista.indice_patente_f4 = -1
        vista.input_patente.text.return_value = "AB"
        filas = [
            {"id_ingreso": 1, "patente": "ABC123", "estado": "ABIERTO", "fecha_hora_ingreso": "2026-01-01 09:00:00", "fecha_hora_salida": None},
            {"id_ingreso": 2, "patente": "ABD123", "estado": "ABIERTO", "fecha_hora_ingreso": "2026-01-01 10:00:00", "fecha_hora_salida": None},
        ]
        vista.formatear_fecha_hora_info.side_effect = lambda valor: str(valor or "-")

        with patch("views.registro.obtener_patentes_turno_actual_para_f4", return_value=filas), \
             patch("views.registro.ordenar_patentes_turno_para_f4", return_value=filas):
            RegistroWindow.seleccionar_siguiente_patente_turno(vista)
            RegistroWindow.seleccionar_siguiente_patente_turno(vista)

        self.assertEqual(vista.input_patente.setText.call_args_list[0].args[0], "ABC123")
        self.assertEqual(vista.input_patente.setText.call_args_list[1].args[0], "ABD123")

    def test_solo_edicion_humana_reinicia_la_sesion_f4(self):
        vista = type("SesionF4", (), {})()
        vista.busqueda_f4 = "AB"
        vista.patentes_f4 = ["candidato"]
        vista.indice_patente_f4 = 1
        input_patente = QLineEdit()
        input_patente.textEdited.connect(
            lambda texto: RegistroWindow.reiniciar_busqueda_f4(vista, texto)
        )

        input_patente.setText("ABC123")

        self.assertEqual(vista.busqueda_f4, "AB")
        self.assertEqual(vista.patentes_f4, ["candidato"])
        self.assertEqual(vista.indice_patente_f4, 1)

        input_patente.textEdited.emit("ABC124")

        self.assertEqual(vista.busqueda_f4, "ABC124")
        self.assertEqual(vista.patentes_f4, [])
        self.assertEqual(vista.indice_patente_f4, -1)


class RegistroViewPreviewIngresoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @patch("views.registro.datetime")
    def test_muestra_preview_de_nuevo_ingreso_sin_datos_de_salida(self, datetime_mock):
        ahora = datetime(2026, 7, 30, 14, 45)
        datetime_mock.now.return_value = ahora
        vista = type("VistaPreviewIngreso", (), {})()
        vista.hora_consulta_label = QLabel()
        vista.formatear_hora_info = lambda valor: valor.strftime("%H:%M")

        RegistroWindow.mostrar_preview_ingreso(vista, "ABC123")

        self.assertEqual(vista.hora_consulta_label.objectName(), "PreviewSalida")
        self.assertEqual(vista.hora_consulta_label.text(), "\n".join([
            "NUEVO INGRESO",
            "Patente: ABC123",
            "Hora de ingreso: 14:45",
            "El ingreso se registra al confirmar la operación.",
        ]))

    def test_muestra_preview_de_salida_solo_con_horas(self):
        vista = type("VistaPreviewSalida", (), {})()
        vista.hora_consulta_label = QLabel()
        vista.formatear_hora_info = RegistroWindow.formatear_hora_info.__get__(vista)
        preview = {
            "patente": "ABC123",
            "fecha_hora_ingreso": datetime(2026, 7, 30, 9, 15),
            "fecha_hora_salida": "2026-07-30 14:45:00",
            "minutos": 330,
            "tarifa_estacionamiento": 2500,
            "total_lavados": 0,
            "tarifa": 2500,
            "noches_prepagadas": [{
                "monto_snapshot": 5000,
                "hora_inicio_snapshot": "22:00",
                "hora_fin_snapshot": "08:00",
            }],
        }

        RegistroWindow.mostrar_preview_salida(vista, preview)

        self.assertEqual(vista.hora_consulta_label.text(), "\n".join([
            "VEHÍCULO DENTRO",
            "Patente: ABC123",
            "Ingreso: 09:15",
            "Consulta de salida: 14:45",
            "Tiempo facturable: 330 min",
            "Estacionamiento: $2500",
            "Noche pagada: $5000",
            "Ventana Noche: 22:00 a 08:00",
            "A COBRAR AHORA: $2500",
            "El importe se recalcula al registrar la salida.",
        ]))


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
