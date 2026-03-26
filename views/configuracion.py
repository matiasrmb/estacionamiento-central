from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QComboBox, QMessageBox,
    QGridLayout, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt

from controllers.config_controller import obtener_configuracion, actualizar_configuracion
from controllers.tarifas_controller import generar_tramos_automaticos


class ConfiguracionWindow(QWidget):
    """
    Vista de configuración general del sistema.
    Permite definir modo de cobro, tarifas base y generar tramos automáticos.
    """

    def __init__(self):
        super().__init__()
        self.setMinimumSize(900, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        titulo = QLabel("Configuración")
        titulo.setObjectName("TituloVentana")
        titulo.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        titulo.setWordWrap(True)
        layout.addWidget(titulo)

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

        label_minuto = QLabel("Tarifa por minuto (CLP)")
        label_minuto.setObjectName("EtiquetaFormulario")
        self.minuto_input = QLineEdit(self.config.get("valor_minuto", "25"))
        self.minuto_input.setMinimumHeight(38)

        label_hora = QLabel("Tarifa por hora (CLP)")
        label_hora.setObjectName("EtiquetaFormulario")
        self.hora_input = QLineEdit(self.config.get("tarifa_hora", "1300"))
        self.hora_input.setMinimumHeight(38)

        layout_general.addWidget(label_modo, 0, 0)
        layout_general.addWidget(self.modo_combo, 0, 1)
        layout_general.addWidget(label_minima, 1, 0)
        layout_general.addWidget(self.minima_input, 1, 1)
        layout_general.addWidget(label_minuto, 2, 0)
        layout_general.addWidget(self.minuto_input, 2, 1)
        layout_general.addWidget(label_hora, 3, 0)
        layout_general.addWidget(self.hora_input, 3, 1)

        layout_general.setColumnStretch(1, 1)

        layout_general_wrapper.addLayout(layout_general)
        layout.addWidget(panel_general)

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

        self.setLayout(layout)

    def guardar(self):
        modo = self.modo_combo.currentText()
        tarifa_minima = self.minima_input.text().strip()
        valor_minuto = self.minuto_input.text().strip()
        tarifa_hora = self.hora_input.text().strip()

        if not tarifa_minima.isdigit() or not valor_minuto.isdigit() or not tarifa_hora.isdigit():
            QMessageBox.warning(self, "Error", "Tarifas deben ser números enteros.")
            return

        actualizar_configuracion("modo_cobro", modo)
        actualizar_configuracion("tarifa_minima", tarifa_minima)
        actualizar_configuracion("tarifa_hora", tarifa_hora)
        actualizar_configuracion("valor_minuto", valor_minuto)

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
            QMessageBox.information(self, "Éxito", "Tramos generados correctamente.")