from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QComboBox, QMessageBox
)
from controllers.config_controller import obtener_configuracion, actualizar_configuracion
from controllers.tarifas_controller import generar_tramos_automaticos

class ConfiguracionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuración del Sistema")
        self.setFixedSize(400, 300)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.config = obtener_configuracion()

        # Modo de cobro
        self.modo_label = QLabel("Modo de cobro:")
        self.modo_combo = QComboBox()
        self.modo_combo.addItems(["minuto", "personalizado"])
        self.modo_combo.setCurrentText(self.config.get("modo_cobro", "minuto"))

        # Tarifa mínima
        self.minima_label = QLabel("Tarifa mínima (CLP):")
        self.minima_input = QLineEdit(self.config.get("tarifa_minima", "300"))

        # Tarifa por hora
        self.hora_label = QLabel("Tarifa por hora (CLP):")
        self.hora_input = QLineEdit(self.config.get("tarifa_hora", "1300"))

        # Guardar
        self.btn_guardar = QPushButton("Guardar configuración")
        self.btn_guardar.clicked.connect(self.guardar)

        self.btn_generar_tramos = QPushButton("🛠 Generar tramos automáticamente")
        self.btn_generar_tramos.clicked.connect(self.generar_tramos_auto)
        layout.addWidget(self.btn_generar_tramos)

        layout.addWidget(self.modo_label)
        layout.addWidget(self.modo_combo)
        layout.addWidget(self.minima_label)
        layout.addWidget(self.minima_input)
        layout.addWidget(self.hora_label)
        layout.addWidget(self.hora_input)
        layout.addWidget(self.btn_guardar)

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
