import os
from pathlib import Path
from fpdf import FPDF

from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QComboBox, QMessageBox,
    QGridLayout, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt

from controllers.config_controller import obtener_configuracion, actualizar_configuracion
from controllers.tarifas_controller import generar_tramos_automaticos
from utils.printer_manager import (obtener_impresoras_instaladas, 
                                   obtener_impresora_predeterminada,
                                   cargar_impresora_guardada,
                                   guardar_impresora_tickets,
)
from utils.ticket import imprimir_pdf_directamente

class ConfiguracionWindow(QWidget):
    """
    Vista de configuración general del sistema.
    Permite definir modo de cobro, tarifas base y generar tramos automáticos.
    """

    def __init__(self, on_tramos_actualizados=None):
        super().__init__()
        self.on_tramos_actualizados = on_tramos_actualizados
        self.setMinimumSize(900, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        subtitulo = QLabel("Define el modo de cobro y las tarifas base del estacionamiento.")
        subtitulo.setObjectName("SubtituloSeccion")
        subtitulo.setWordWrap(True)
        layout.addWidget(subtitulo)

        self.config = obtener_configuracion()

        # =========================================================
        # CONFIGURACIÓN GENERAL
        # =========================================================
        panel_general = QFrame()
        panel_general.setObjectName("PanelFormulario")
        layout_general_wrapper = QVBoxLayout(panel_general)
        layout_general_wrapper.setContentsMargins(14, 14, 14, 14)
        layout_general_wrapper.setSpacing(10)

        titulo_general = QLabel("Configuración general")
        titulo_general.setObjectName("EtiquetaFormulario")
        layout_general_wrapper.addWidget(titulo_general)

        layout_general = QGridLayout()
        layout_general.setHorizontalSpacing(14)
        layout_general.setVerticalSpacing(12)

        label_modo = QLabel("Modo de cobro")
        label_modo.setObjectName("EtiquetaFormulario")
        self.modo_combo = QComboBox()
        self.modo_combo.addItems(["minuto", "personalizado", "auto"])
        self.modo_combo.setCurrentText(self.config.get("modo_cobro", "minuto"))
        self.modo_combo.setMinimumHeight(38)

        label_minima = QLabel("Tarifa mínima (CLP)")
        label_minima.setObjectName("EtiquetaFormulario")
        self.minima_input = QLineEdit(self.config.get("tarifa_minima", "300"))
        self.minima_input.setMinimumHeight(38)
        self.minima_input.returnPressed.connect(self.guardar)

        label_minuto = QLabel("Tarifa por minuto (CLP)")
        label_minuto.setObjectName("EtiquetaFormulario")
        self.minuto_input = QLineEdit(self.config.get("valor_minuto", "25"))
        self.minuto_input.setMinimumHeight(38)
        self.minuto_input.returnPressed.connect(self.guardar)

        label_hora = QLabel("Tarifa por hora (CLP)")
        label_hora.setObjectName("EtiquetaFormulario")
        self.hora_input = QLineEdit(self.config.get("tarifa_hora", "1300"))
        self.hora_input.setMinimumHeight(38)
        self.hora_input.returnPressed.connect(self.guardar)

        label_bano = QLabel("Valor uso de baño (CLP)")
        label_bano.setObjectName("EtiquetaFormulario")
        self.bano_input = QLineEdit(self.config.get("valor_bano", "300"))
        self.bano_input.setMinimumHeight(38)
        self.bano_input.returnPressed.connect(self.guardar)

        layout_general.addWidget(label_modo, 0, 0)
        layout_general.addWidget(self.modo_combo, 0, 1)
        layout_general.addWidget(label_minima, 1, 0)
        layout_general.addWidget(self.minima_input, 1, 1)
        layout_general.addWidget(label_minuto, 2, 0)
        layout_general.addWidget(self.minuto_input, 2, 1)
        layout_general.addWidget(label_hora, 3, 0)
        layout_general.addWidget(self.hora_input, 3, 1)
        layout_general.addWidget(label_bano, 4, 0)
        layout_general.addWidget(self.bano_input, 4, 1)

        layout_general.setColumnStretch(1, 1)

        layout_general_wrapper.addLayout(layout_general)
        layout.addWidget(panel_general)

        # =========================================================
        # IMPRESIÓN DE TICKETS
        # =========================================================
        panel_impresion = QFrame()
        panel_impresion.setObjectName("PanelFormulario")
        layout_impresion_wrapper = QVBoxLayout(panel_impresion)
        layout_impresion_wrapper.setContentsMargins(14, 14, 14, 14)
        layout_impresion_wrapper.setSpacing(10)

        titulo_impresion = QLabel("Impresión de tickets")
        titulo_impresion.setObjectName("EtiquetaFormulario")
        layout_impresion_wrapper.addWidget(titulo_impresion)

        descripcion_impresion = QLabel(
            "Selecciona la impresora que se utilizará para los tickets térmicos. "
            "Si la impresora configurada deja de existir, el sistema intentará usar "
            "la impresora predeterminada de Windows."
        )
        descripcion_impresion.setWordWrap(True)
        descripcion_impresion.setObjectName("SubtituloSeccion")
        layout_impresion_wrapper.addWidget(descripcion_impresion)

        layout_impresion = QGridLayout()
        layout_impresion.setHorizontalSpacing(14)
        layout_impresion.setVerticalSpacing(12)

        label_impresora = QLabel("Impresora de tickets")
        label_impresora.setObjectName("EtiquetaFormulario")

        self.impresora_combo = QComboBox()
        self.impresora_combo.setMinimumHeight(38)

        self.btn_actualizar_impresoras = QPushButton("Actualizar lista")
        self.btn_actualizar_impresoras.setMinimumHeight(38)
        self.btn_actualizar_impresoras.clicked.connect(self.cargar_impresoras_en_combo)

        self.btn_guardar_impresora = QPushButton("Guardar impresora")
        self.btn_guardar_impresora.setMinimumHeight(38)
        self.btn_guardar_impresora.clicked.connect(self.guardar_impresora_seleccionada)

        self.btn_probar_impresion = QPushButton("Probar impresión")
        self.btn_probar_impresion.setMinimumHeight(38)
        self.btn_probar_impresion.clicked.connect(self.probar_impresion_ticket)

        layout_impresion.addWidget(label_impresora, 0, 0)
        layout_impresion.addWidget(self.impresora_combo, 0, 1)
        layout_impresion.addWidget(self.btn_actualizar_impresoras, 0, 2)
        layout_impresion.addWidget(self.btn_guardar_impresora, 1, 1)
        layout_impresion.addWidget(self.btn_probar_impresion, 1, 2)

        layout_impresion.setColumnStretch(1, 1)

        layout_impresion_wrapper.addLayout(layout_impresion)
        layout.addWidget(panel_impresion)

        # =========================================================
        # ACCIONES
        # =========================================================
        panel_acciones = QFrame()
        panel_acciones.setObjectName("PanelFormulario")
        layout_acciones_wrapper = QVBoxLayout(panel_acciones)
        layout_acciones_wrapper.setContentsMargins(14, 14, 14, 14)
        layout_acciones_wrapper.setSpacing(10)

        titulo_acciones = QLabel("Acciones disponibles")
        titulo_acciones.setObjectName("EtiquetaFormulario")
        layout_acciones_wrapper.addWidget(titulo_acciones)

        self.btn_generar_tramos = QPushButton("Generar tramos automáticamente")
        self.btn_generar_tramos.setMinimumHeight(40)
        self.btn_generar_tramos.clicked.connect(self.generar_tramos_auto)

        self.btn_guardar = QPushButton("Guardar configuración")
        self.btn_guardar.setMinimumHeight(40)
        self.btn_guardar.clicked.connect(self.guardar)

        layout_acciones_wrapper.addWidget(self.btn_generar_tramos)
        layout_acciones_wrapper.addWidget(self.btn_guardar)

        layout.addWidget(panel_acciones)
        layout.addStretch()

        self.cargar_impresoras_en_combo()
        self.setLayout(layout)

    def cargar_impresoras_en_combo(self):
        """
        Carga las impresoras instaladas en el QComboBox y selecciona
        la guardada o la predeterminada si corresponde.
        """
        self.impresora_combo.clear()

        impresoras = obtener_impresoras_instaladas()
        if not impresoras:
            self.impresora_combo.addItem("No hay impresoras disponibles")
            self.impresora_combo.setEnabled(False)
            self.btn_guardar_impresora.setEnabled(False)
            self.btn_probar_impresion.setEnabled(False)
            return

        self.impresora_combo.setEnabled(True)
        self.btn_guardar_impresora.setEnabled(True)
        self.btn_probar_impresion.setEnabled(True)

        self.impresora_combo.addItems(impresoras)

        impresora_guardada = cargar_impresora_guardada()
        impresora_default = obtener_impresora_predeterminada()

        if impresora_guardada and impresora_guardada in impresoras:
            self.impresora_combo.setCurrentText(impresora_guardada)
        elif impresora_default and impresora_default in impresoras:
            self.impresora_combo.setCurrentText(impresora_default)

    def guardar_impresora_seleccionada(self):
        """
        Guarda la impresora actualmente seleccionada en config.ini.
        """
        impresora = self.impresora_combo.currentText().strip()

        if not impresora or impresora == "No hay impresoras disponibles":
            QMessageBox.warning(
                self,
                "Error",
                "No hay una impresora válida para guardar."
            )
            return

        guardar_impresora_tickets(impresora)
        QMessageBox.information(
            self,
            "Guardado",
            f"Impresora de tickets guardada correctamente:\n{impresora}"
        )

    def probar_impresion_ticket(self):
        """
        Genera un ticket de prueba sencillo y lo envía a imprimir
        usando la impresora seleccionada.
        """
        impresora = self.impresora_combo.currentText().strip()

        if not impresora or impresora == "No hay impresoras disponibles":
            QMessageBox.warning(
                self,
                "Error",
                "No hay una impresora válida seleccionada."
            )
            return

        try:
            carpeta = Path("tickets")
            carpeta.mkdir(exist_ok=True)

            ruta_pdf = carpeta / "ticket_prueba_impresora.pdf"

            pdf = FPDF(format=(58, 90), unit="mm")
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=4)
            pdf.set_font("Courier", size=9)

            pdf.cell(0, 5, "ESTACIONAMIENTO CENTRAL", ln=True, align="C")
            pdf.cell(0, 5, "Ticket de Prueba", ln=True, align="C")
            pdf.cell(0, 4, "-" * 28, ln=True, align="C")
            pdf.cell(0, 5, f"Impresora:", ln=True)
            pdf.multi_cell(0, 5, impresora)
            pdf.cell(0, 5, "Estado: prueba correcta", ln=True)
            pdf.cell(0, 5, "Gracias por su visita", ln=True, align="C")

            pdf.output(str(ruta_pdf))

            exito = imprimir_pdf_directamente(str(ruta_pdf), impresora)

            if exito:
                QMessageBox.information(
                    self,
                    "Prueba enviada",
                    f"Se envió un ticket de prueba a:\n{impresora}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "No se pudo enviar la impresión de prueba."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error de impresión",
                f"Ocurrió un error al generar o imprimir el ticket de prueba:\n{e}"
            )

    def guardar(self):
        modo = self.modo_combo.currentText()
        tarifa_minima = self.minima_input.text().strip()
        valor_minuto = self.minuto_input.text().strip()
        tarifa_hora = self.hora_input.text().strip()
        valor_bano = self.bano_input.text().strip()

        if (
            not tarifa_minima.isdigit() 
            or not valor_minuto.isdigit() 
            or not tarifa_hora.isdigit() 
            or not valor_bano.isdigit()
        ):
            QMessageBox.warning(self, "Error", "Tarifas deben ser números enteros.")
            return

        actualizar_configuracion("modo_cobro", modo)
        actualizar_configuracion("tarifa_minima", tarifa_minima)
        actualizar_configuracion("tarifa_hora", tarifa_hora)
        actualizar_configuracion("valor_minuto", valor_minuto)
        actualizar_configuracion("valor_bano", valor_bano)

        QMessageBox.information(self, "Guardado", "Configuración actualizada correctamente.")

    def generar_tramos_auto(self):
        confirmar = QMessageBox.question(
            self,
            "Confirmación",
            "¿Deseas generar automáticamente los tramos de tarifas personalizados?\nEsto sobrescribirá los tramos actuales.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirmar == QMessageBox.Yes:
            generar_tramos_automaticos()
            actualizar_configuracion("modo_auto_simplificado", 1)

            if callable(self.on_tramos_actualizados):
                self.on_tramos_actualizados()

            QMessageBox.information(self, "Éxito", "Tramos generados correctamente.")