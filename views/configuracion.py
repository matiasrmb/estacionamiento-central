from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QComboBox, QMessageBox, QGroupBox,
    QGridLayout, QHBoxLayout, QFrame
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
        layout.setSpacing(16)

        titulo = QLabel("Configuración del sistema")
        titulo.setObjectName("TituloVentana")
        titulo.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(titulo)

        subtitulo = QLabel("Define el modo de cobro y las tarifas base del estacionamiento.")
        subtitulo.setObjectName("SubtituloSeccion")
        subtitulo.setWordWrap(True)
        layout.addWidget(subtitulo)

        self.config = obtener_configuracion()

        # =========================================================
        # CONFIGURACIÓN GENERAL
        # =========================================================
        grupo_general = QGroupBox("Configuración general")
        layout_general = QGridLayout()
        layout_general.setContentsMargins(14, 20, 14, 20)
        layout_general.setHorizontalSpacing(14)
        layout_general.setVerticalSpacing(12)

        label_modo = QLabel("Modo de cobro:")
        label_modo.setObjectName("EtiquetaFormulario")
        self.modo_combo = QComboBox()
        self.modo_combo.addItems(["minuto", "personalizado"])
        self.modo_combo.setCurrentText(self.config.get("modo_cobro", "minuto"))
        self.modo_combo.setMinimumHeight(38)

        label_minima = QLabel("Tarifa mínima (CLP):")
        label_minima.setObjectName("EtiquetaFormulario")
        self.minima_input = QLineEdit(self.config.get("tarifa_minima", "300"))
        self.minima_input.setMinimumHeight(38)

        label_hora = QLabel("Tarifa por hora (CLP):")
        label_hora.setObjectName("EtiquetaFormulario")
        self.hora_input = QLineEdit(self.config.get("tarifa_hora", "1300"))
        self.hora_input.setMinimumHeight(38)

        layout_general.addWidget(label_modo, 0, 0)
        layout_general.addWidget(self.modo_combo, 0, 1)
        layout_general.addWidget(label_minima, 1, 0)
        layout_general.addWidget(self.minima_input, 1, 1)
        layout_general.addWidget(label_hora, 2, 0)
        layout_general.addWidget(self.hora_input, 2, 1)

        layout_general.setColumnStretch(1, 1)
        grupo_general.setLayout(layout_general)
        layout.addWidget(grupo_general)

        # =========================================================
        # ACCIONES
        # =========================================================
        grupo_acciones = QGroupBox("Acciones disponibles")
        layout_acciones = QVBoxLayout()
        layout_acciones.setContentsMargins(14, 20, 14, 20)
        layout_acciones.setSpacing(12)

        self.btn_generar_tramos = QPushButton("Generar tramos automáticamente")
        self.btn_generar_tramos.setMinimumHeight(40)
        self.btn_generar_tramos.clicked.connect(self.generar_tramos_auto)

        self.btn_guardar = QPushButton("Guardar configuración")
        self.btn_guardar.setMinimumHeight(40)
        self.btn_guardar.clicked.connect(self.guardar)

        layout_acciones.addWidget(self.btn_generar_tramos)
        layout_acciones.addWidget(self.btn_guardar)

        grupo_acciones.setLayout(layout_acciones)
        layout.addWidget(grupo_acciones)

        layout.addStretch()
        self.setLayout(layout)

    def guardar(self):
        modo = self.modo_combo.currentText()
        tarifa_minima = self.minima_input.text().strip()
        tarifa_hora = self.hora_input.text().strip()

        if not tarifa_minima.isdigit() or not tarifa_hora.isdigit():
            QMessageBox.warning(self, "Error", "Tarifas deben ser números enteros.")
            return

        actualizar_configuracion("modo_cobro", modo)
        actualizar_configuracion("tarifa_minima", tarifa_minima)
        actualizar_configuracion("tarifa_hora", tarifa_hora)

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