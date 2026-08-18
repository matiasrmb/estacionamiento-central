import os
import unittest
from datetime import datetime
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import QApplication, QLabel, QLineEdit
from views.admin_edicion import EdicionIngresosWindow
from views.registro import (
    QMessageBox, REGISTRO_METRICAS, RegistroWindow, TarjetaResumen,
    calcular_metricas_resumen, construir_info_patente_navegada,
    construir_mensaje_ingreso, construir_mensaje_salida,
)


class RegistroMetricCardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_privacidad_esta_desactivada_por_defecto(self):
        tarjeta = TarjetaResumen("Total turno", "$5000", "total-turno.svg")

        self.assertEqual(tarjeta.label_valor.text(), "$5000")
        self.assertFalse(tarjeta.label_valor.isHidden())
        self.assertFalse(tarjeta.label_icono.isHidden())
        self.assertEqual(tarjeta.icono_archivo, "total-turno.svg")
        self.assertFalse(tarjeta.label_icono.pixmap().isNull())
        self.assertTrue(tarjeta.label_privacidad.isHidden())

    def test_privacidad_oculta_y_revela_el_valor_al_pasarlo_con_el_mouse(self):
        tarjeta = TarjetaResumen(
            "Total turno",
            "$5000",
            "neto-caja.svg",
            ayuda="Cobrado desde último cierre",
            modo_privacidad=True,
        )

        self.assertEqual(tarjeta.label_titulo.text(), "Total turno")
        self.assertFalse(tarjeta.label_titulo.isHidden())
        self.assertEqual(tarjeta.label_ayuda.text(), "i")
        self.assertEqual(tarjeta.label_ayuda.toolTip(), "Cobrado desde último cierre")
        self.assertEqual(tarjeta.label_titulo.toolTip(), "Cobrado desde último cierre")
        self.assertEqual(tarjeta.label_valor.text(), "")
        self.assertTrue(tarjeta.label_valor.isHidden())
        self.assertTrue(tarjeta.label_icono.isHidden())
        self.assertFalse(tarjeta.label_privacidad.isHidden())
        self.assertFalse(tarjeta.label_privacidad.pixmap().isNull())
        self.assertEqual(tarjeta.label_privacidad.objectName(), "IconoPrivacidadResumenModulo")
        self.assertNotIn("Oculto", [label.text() for label in tarjeta.findChildren(QLabel)])
        tarjeta.enterEvent(QEnterEvent(QPointF(), QPointF(), QPointF()))
        self.assertEqual(tarjeta.label_valor.text(), "$5000")
        self.assertFalse(tarjeta.label_valor.isHidden())
        self.assertFalse(tarjeta.label_icono.isHidden())
        self.assertTrue(tarjeta.label_privacidad.isHidden())
        tarjeta.leaveEvent(QEvent(QEvent.Leave))
        self.assertEqual(tarjeta.label_valor.text(), "")
        self.assertTrue(tarjeta.label_valor.isHidden())
        self.assertTrue(tarjeta.label_icono.isHidden())
        self.assertFalse(tarjeta.label_privacidad.isHidden())

    def test_tarjetas_mantienen_altura_fija_en_privacidad_y_al_revelar(self):
        tarjeta = TarjetaResumen(
            "Total proyectado",
            "$5000",
            "total-proyectado.svg",
            modo_privacidad=True,
        )

        self.assertEqual(tarjeta.minimumHeight(), 112)
        self.assertEqual(tarjeta.maximumHeight(), 112)
        tarjeta.enterEvent(QEnterEvent(QPointF(), QPointF(), QPointF()))
        self.assertEqual(tarjeta.height(), 112)

    def test_titulo_permanece_alineado_arriba_al_revelar_privacidad(self):
        tarjeta = TarjetaResumen(
            "Total proyectado",
            "$5000",
            "total-proyectado.svg",
            modo_privacidad=True,
        )

        self.assertEqual(tarjeta.label_titulo.alignment(), Qt.AlignLeft | Qt.AlignTop)
        tarjeta.enterEvent(QEnterEvent(QPointF(), QPointF(), QPointF()))
        self.assertEqual(tarjeta.label_titulo.alignment(), Qt.AlignLeft | Qt.AlignTop)

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

    def test_total_proyectado_del_registro_incluye_servicios_activos(self):
        vista = Mock()
        vista.subida_vigente_ahora.return_value = False
        vista._fila_solo_lavado.return_value = {
            "patente": "Solo lavado: ABC123",
            "hora": "12/08/2026 10:00",
            "monto": 3000,
            "minutos": 0,
            "tipo_fila": "solo_lavado",
        }
        vista.tabla_activos = Mock()
        vista.grupo_tabla = Mock()
        vista.label_leyenda_tabla = Mock()
        vista.aplicar_estilo_fila_total = Mock()
        vista.card_estacionados = Mock()
        vista.card_total_activos = Mock()
        vista.card_total_proyectado = Mock()
        vista.card_total_turno = Mock()
        vista.card_neto_caja = Mock()
        vista.card_banos = Mock()

        with patch("views.registro.obtener_vehiculos_activos", return_value=[{
            "patente": "AAA111",
            "hora": "12/08/2026 09:00",
            "monto": 5000,
            "minutos": 60,
        }]), patch("views.registro.obtener_solo_lavados_activos", return_value=[{"id_operacion_servicio": 7}]), \
             patch("views.registro.obtener_resumen_banos", return_value={"cantidad": 0, "total": 0}), \
             patch("views.registro.obtener_resumen_caja_actual", return_value={"total_general": 10000, "total_neto": 9000}):
            RegistroWindow.actualizar_tabla_activos(vista)

        vista.card_total_activos.set_valor.assert_called_with("$8000")
        vista.card_total_proyectado.set_valor.assert_called_with("$18000")


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

    def test_f4_formatea_ingreso_y_salida_solo_con_horas(self):
        vista = Mock()
        vista.busqueda_f4 = ""
        vista.patentes_f4 = []
        vista.indice_patente_f4 = -1
        vista.formatear_hora_info.side_effect = lambda valor: str(valor)[11:16] if valor else "-"
        fila = {
            "id_ingreso": 1,
            "patente": "ABC123",
            "estado": "CERRADO",
            "fecha_hora_ingreso": "2026-07-30 09:15:00",
            "fecha_hora_salida": "2026-07-30 14:45:00",
            "minutos": 330,
            "monto": 2500,
        }

        with patch("views.registro.obtener_patentes_turno_actual_para_f4", return_value=[fila]), \
             patch("views.registro.ordenar_patentes_turno_para_f4", return_value=[fila]):
            RegistroWindow.seleccionar_siguiente_patente_turno(vista)

        vista.mostrar_info_patente_navegada.assert_called_once_with(
            tecla="F4", posicion=1, total=1, patente="ABC123", estado="CERRADO",
            ingreso="09:15", salida="14:45", minutos=330, monto=2500,
        )

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

    def test_f3_formatea_el_ingreso_solo_con_hora(self):
        vista = Mock()
        vista.busqueda_f3 = ""
        vista.patentes_f3 = []
        vista.indice_patente_f3 = -1
        vista.formatear_hora_info.return_value = "09:15"
        fila = {
            "id_ingreso": 1,
            "patente_base": "ABC123",
            "patente": "ABC123",
            "hora": "2026-07-30 09:15:00",
        }

        with patch("views.registro.obtener_vehiculos_activos", return_value=[fila]):
            RegistroWindow.seleccionar_siguiente_patente_abierta(vista)

        vista.mostrar_info_patente_navegada.assert_called_once_with(
            tecla="F3", posicion=1, total=1, patente="ABC123", estado="ABIERTO",
            ingreso="09:15", salida="Aún dentro", minutos=0, monto=0,
        )

    def test_f3_conserva_marcadores_de_espera_y_lavado(self):
        vista = Mock()
        vista.busqueda_f3 = ""
        vista.patentes_f3 = []
        vista.indice_patente_f3 = -1
        vista.formatear_hora_info.return_value = "09:15"
        fila = {
            "id_ingreso": 1,
            "patente_base": "ABC123",
            "patente": "ABC123",
            "hora": "2026-07-30 09:15:00",
            "minutos": 45,
            "monto": 1200,
            "en_espera": True,
            "en_lavado": True,
        }

        with patch("views.registro.obtener_vehiculos_activos", return_value=[fila]):
            RegistroWindow.seleccionar_siguiente_patente_abierta(vista)

        vista.mostrar_info_patente_navegada.assert_called_once_with(
            tecla="F3", posicion=1, total=1, patente="ABC123",
            estado="ABIERTO (EN ESPERA, EN LAVADO)",
            ingreso="09:15", salida="Aún dentro", minutos=45, monto=1200,
        )


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
    def test_info_f3_f4_usa_jerarquia_vertical_y_distingue_total_cerrado(self):
        mensaje = construir_info_patente_navegada(
            "F4", 2, 3, "ABC123", "CERRADO", "09:15", "14:45", 330, 2500,
        )

        self.assertEqual(mensaje, "\n".join([
            "F4 2/3",
            "Patente: ABC123",
            "Estado: CERRADO",
            "Ingreso: 09:15",
            "Salida: 14:45",
            "Tiempo: 330 min",
            "Total: $2500",
        ]))
        self.assertNotIn("|", mensaje)
        self.assertNotIn("2026-07-30", mensaje)

    def test_info_f3_f4_usa_monto_actual_para_estado_abierto(self):
        mensaje = construir_info_patente_navegada(
            "F3", 1, 4, "ABC123", "ABIERTO (EN ESPERA)", "09:15", "Aún dentro", 45, 1200,
        )

        self.assertIn("Estado: ABIERTO (EN ESPERA)", mensaje)
        self.assertIn("Monto actual: $1200", mensaje)
        self.assertNotIn("Total: $1200", mensaje)

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
