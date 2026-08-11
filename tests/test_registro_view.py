import os
import unittest
from datetime import datetime
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QPointF
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import QApplication, QLabel, QLineEdit
from views.admin_edicion import EdicionIngresosWindow
from views.registro import (
    QMessageBox, REGISTRO_METRICAS, RegistroWindow, TarjetaResumen,
    calcular_metricas_resumen, construir_mensaje_ingreso, construir_mensaje_salida,
)


class RegistroMetricCardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_privacidad_esta_desactivada_por_defecto(self):
        tarjeta = TarjetaResumen("Total turno", "$5000", "$")

        self.assertEqual(tarjeta.label_valor.text(), "$5000")

    def test_privacidad_oculta_y_revela_el_valor_al_pasarlo_con_el_mouse(self):
        tarjeta = TarjetaResumen("Total turno", "$5000", "$", modo_privacidad=True)

        self.assertEqual(tarjeta.label_valor.text(), "Oculto")
        tarjeta.enterEvent(QEnterEvent(QPointF(), QPointF(), QPointF()))
        self.assertEqual(tarjeta.label_valor.text(), "$5000")
        tarjeta.leaveEvent(QEvent(QEvent.Leave))
        self.assertEqual(tarjeta.label_valor.text(), "Oculto")

    def test_orden_y_formulas_de_metricas_del_registro(self):
        metricas = calcular_metricas_resumen(1250, {"total_general": 5000, "total_neto": 4400})

        self.assertEqual(REGISTRO_METRICAS, (
            "Vehículos activos",
            "Usos de baño hoy",
            "Estimado activos",
            "Total proyectado",
            "Total turno",
            "Neto en caja",
        ))
        self.assertEqual(metricas["estimado_activos"], 1250)
        self.assertEqual(metricas["total_proyectado"], 6250)
        self.assertEqual(metricas["total_turno"], 5000)
        self.assertEqual(metricas["neto_caja"], 4400)


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

    def test_f8_con_ingreso_abierto_conserva_el_alternado_actual(self):
        vista = Mock()
        vista.input_patente.text.return_value = "ABC123"
        vista.validar_patente.return_value = (True, "")
        vista.seleccion_f4 = {"id_ingreso": 10, "patente": "ABC123", "estado": "ABIERTO"}

        with patch("views.registro.alternar_estado_espera", return_value=(True, "En espera.")) as alternar, \
             patch("views.registro.enviar_salida_sin_cobro_a_espera") as enviar, \
             patch("views.registro.QMessageBox.information"):
            RegistroWindow.alternar_espera_desde_tecla(vista)

        alternar.assert_called_once_with("ABC123")
        enviar.assert_not_called()

    def test_f8_envia_el_cerrado_seleccionado_por_f4_a_espera(self):
        vista = Mock()
        vista.usuario = "operador"
        vista.input_patente.text.return_value = "ABC123"
        vista.validar_patente.return_value = (True, "")
        vista.seleccion_f4 = {"id_ingreso": 42, "patente": "ABC123", "estado": "CERRADO"}

        with patch("views.registro.enviar_salida_sin_cobro_a_espera", return_value=(True, "En espera.")) as enviar, \
             patch("views.registro.alternar_estado_espera") as alternar, \
             patch("views.registro.QMessageBox.question", return_value=QMessageBox.Yes), \
             patch("views.registro.QMessageBox.information"):
            RegistroWindow.alternar_espera_desde_tecla(vista)

        enviar.assert_called_once_with(42, "operador", True, patente_esperada="ABC123")
        alternar.assert_not_called()

    def test_f8_para_ticket_impreso_pide_confirmacion_adicional(self):
        vista = Mock()
        vista.usuario = "operador"
        vista.input_patente.text.return_value = "ABC123"
        vista.validar_patente.return_value = (True, "")
        vista.seleccion_f4 = {"id_ingreso": 42, "patente": "ABC123", "estado": "CERRADO"}

        with patch(
            "views.registro.enviar_salida_sin_cobro_a_espera",
            side_effect=[(False, "El ticket de salida ya fue impreso."), (True, "En espera.")],
        ) as enviar, patch(
            "views.registro.QMessageBox.question", return_value=QMessageBox.Yes
        ), patch("views.registro.QMessageBox.information"):
            RegistroWindow.alternar_espera_desde_tecla(vista)

        self.assertEqual(enviar.call_count, 2)
        self.assertTrue(enviar.call_args_list[1].kwargs["confirma_ticket_impreso"])


class RegistroViewF3Tests(unittest.TestCase):
    def test_f3_con_busqueda_elige_la_patente_mas_similar(self):
        vista = Mock()
        vista.busqueda_f3 = "ABC12"
        vista.patentes_f3 = []
        vista.indice_patente_f3 = -1
        vista.formatear_fecha_hora_info.side_effect = lambda valor: str(valor or "-")
        filas = [
            {"id_ingreso": 1, "patente_base": "ABC123", "patente": "ABC123", "hora": "2026-01-01 09:00:00"},
            {"id_ingreso": 2, "patente_base": "ZZZ999", "patente": "ZZZ999", "hora": "2026-01-01 10:00:00"},
        ]

        with patch("views.registro.obtener_vehiculos_activos", return_value=filas):
            RegistroWindow.seleccionar_siguiente_patente_abierta(vista)

        vista.input_patente.setText.assert_called_once_with("ABC123")

    def test_f3_vacia_ordena_y_selecciona_alfabeticamente(self):
        vista = Mock()
        vista.busqueda_f3 = ""
        vista.patentes_f3 = []
        vista.indice_patente_f3 = -1
        vista.formatear_fecha_hora_info.side_effect = lambda valor: str(valor or "-")
        filas = [
            {"id_ingreso": 1, "patente_base": "ZZZ999", "patente": "ZZZ999", "hora": "2026-01-01 09:00:00"},
            {"id_ingreso": 2, "patente_base": "ABC123", "patente": "ABC123", "hora": "2026-01-01 10:00:00"},
        ]

        with patch("views.registro.obtener_vehiculos_activos", return_value=filas):
            RegistroWindow.seleccionar_siguiente_patente_abierta(vista)

        vista.input_patente.setText.assert_called_once_with("ABC123")


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


class RegistroViewPopupTests(unittest.TestCase):
    def test_popup_ingreso_omite_fecha_y_destaca_patente_y_hora(self):
        mensaje = construir_mensaje_ingreso({
            "patente": "ABC123",
            "fecha_hora_ingreso": datetime(2026, 7, 30, 14, 45),
        })

        self.assertIn('font-size: 14pt', mensaje)
        self.assertIn("Patente: <b>ABC123</b>", mensaje)
        self.assertIn("Ingreso: <b>14:45</b>", mensaje)
        self.assertNotIn("30/07/2026", mensaje)

    def test_popup_salida_muestra_noches_solo_para_ingreso_nocturno(self):
        salida = {
            "patente": "ABC123",
            "fecha_hora_ingreso": datetime(2026, 7, 30, 9, 15),
            "fecha_hora_salida": datetime(2026, 7, 30, 14, 45),
            "minutos": 330,
            "tarifa": 2500,
            "total_noches_prepagadas": 5000,
        }

        normal = construir_mensaje_salida({**salida, "noches_prepagadas": []})
        nocturna = construir_mensaje_salida({**salida, "noches_prepagadas": [{"monto_snapshot": 5000}]})

        self.assertNotIn("Noches ya pagadas", normal)
        self.assertIn("Noches ya pagadas: $5000", nocturna)
        self.assertIn("Ingreso: <b>09:15</b>", normal)
        self.assertIn("Salida: <b>14:45</b>", normal)
        self.assertIn("A cobrar ahora: <b>$2500</b>", normal)
        self.assertNotIn("30/07/2026", normal)

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


class RegistroViewPlateValidationTests(unittest.TestCase):
    def _vista(self, patente):
        vista = Mock()
        vista.input_patente.text.return_value = patente
        vista.usuario = "operador"
        vista.validar_patente = RegistroWindow.validar_patente.__get__(vista)
        return vista

    def test_busca_y_registra_salida_de_patente_historica_con_separador(self):
        vista = self._vista(" ab-12 ")

        with patch("views.registro.buscar_estado_vehiculo", return_value="dentro") as buscar, \
             patch("views.registro.obtener_preview_salida_por_patente", return_value=None):
            RegistroWindow.buscar_vehiculo(vista)

        buscar.assert_called_once_with("AB-12")
        vista.boton_salida.setEnabled.assert_called_once_with(True)

        salida = {
            "patente": "AB-12",
            "fecha_hora_ingreso": datetime(2026, 7, 30, 9, 0),
            "fecha_hora_salida": datetime(2026, 7, 30, 10, 0),
            "minutos": 60,
            "total_noches_prepagadas": 0,
            "tarifa": 1000,
        }
        with patch("views.registro.registrar_salida_detallada", return_value=salida) as registrar, \
             patch("views.registro.QMessageBox.information"):
            RegistroWindow.registrar_salida(vista)

        registrar.assert_called_once_with("AB-12", "operador")

    def test_rechaza_ingreso_nuevo_con_patente_historica_invalida(self):
        vista = self._vista(" ab-12 ")

        with patch("views.registro.registrar_ingreso_detallado") as registrar, \
             patch("views.registro.QMessageBox.warning") as advertir:
            RegistroWindow.registrar_ingreso(vista)

        registrar.assert_not_called()
        advertir.assert_called_once()

    def test_normaliza_patente_canonica_al_registrar_ingreso(self):
        vista = self._vista(" ab-cd 12 ")
        ingreso = {
            "patente": "ABCD12",
            "fecha_hora_ingreso": datetime(2026, 7, 30, 9, 0),
        }

        with patch("views.registro.registrar_ingreso_detallado", return_value=ingreso) as registrar, \
             patch("views.registro.QMessageBox.information"):
            RegistroWindow.registrar_ingreso(vista)

        registrar.assert_called_once_with("ABCD12")


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

    def test_envia_salida_sin_cobro_a_espera_con_confirmacion(self):
        vista = Mock()
        vista.usuario_admin = "administrador"
        vista.tabla.currentRow.return_value = 0
        vista.tabla.item.side_effect = [Mock(text=Mock(return_value="CERRADO")), Mock(text=Mock(return_value="42"))]

        with patch("views.admin_edicion.enviar_salida_sin_cobro_a_espera", return_value=(True, "En espera.")) as enviar, \
             patch("views.admin_edicion.QMessageBox.question", return_value=QMessageBox.Yes), \
             patch("views.admin_edicion.QMessageBox.information"):
            EdicionIngresosWindow.enviar_salida_a_espera(vista)

        enviar.assert_called_once_with(42, "administrador", True)
        vista.cargar_datos.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
