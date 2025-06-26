from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QComboBox, QMessageBox, QGroupBox
)
from controllers.config_controller import obtener_configuracion, actualizar_configuracion
from controllers.tarifas_controller import generar_tramos_automaticos

class ConfiguracionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuración del Sistema")
        self.setMinimumSize(400, 500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.config = obtener_configuracion()

        # 🔧 Grupo de configuración general
        grupo_general = QGroupBox("⚙️ Configuración General")
        layout_general = QVBoxLayout()
        layout_general.setContentsMargins(10, 20, 10, 20)  # Espaciado interno

        self.modo_label = QLabel("Modo de cobro:")
        self.modo_combo = QComboBox()
        self.modo_combo.addItems(["minuto", "personalizado"])
        self.modo_combo.setCurrentText(self.config.get("modo_cobro", "minuto"))

        self.minima_label = QLabel("Tarifa mínima (CLP):")
        self.minima_input = QLineEdit(self.config.get("tarifa_minima", "300"))

        self.hora_label = QLabel("Tarifa por hora (CLP):")
        self.hora_input = QLineEdit(self.config.get("tarifa_hora", "1300"))

        layout_general.addWidget(self.modo_label)
        layout_general.addWidget(self.modo_combo)
        layout_general.addWidget(self.minima_label)
        layout_general.addWidget(self.minima_input)
        layout_general.addWidget(self.hora_label)
        layout_general.addWidget(self.hora_input)

        grupo_general.setLayout(layout_general)
        layout.addWidget(grupo_general)

        # 🛠 Grupo de acciones
        grupo_acciones = QGroupBox("🛠 Acciones disponibles")
        layout_acciones = QVBoxLayout()

        self.btn_generar_tramos = QPushButton("📊 Generar tramos automáticamente")
        self.btn_generar_tramos.clicked.connect(self.generar_tramos_auto)

        self.btn_guardar = QPushButton("💾 Guardar configuración")
        self.btn_guardar.clicked.connect(self.guardar)

        layout_acciones.addWidget(self.btn_generar_tramos)
        layout_acciones.addWidget(self.btn_guardar)

        grupo_acciones.setLayout(layout_acciones)
        layout.addWidget(grupo_acciones)

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
