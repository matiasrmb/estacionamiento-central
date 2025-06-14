from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QHBoxLayout
)
from controllers.mensuales_controller import obtener_mensuales, agregar_mensual

class MensualesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clientes Mensuales")
        self.setFixedSize(500, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Formulario de registro
        self.patente_input = QLineEdit()
        self.patente_input.setPlaceholderText("Patente (ej: ABCD12)")
        self.btn_agregar = QPushButton("Agregar Cliente Mensual")
        self.btn_agregar.clicked.connect(self.agregar_mensual)

        form_layout = QHBoxLayout()
        form_layout.addWidget(self.patente_input)
        form_layout.addWidget(self.btn_agregar)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(2)
        self.tabla.setHorizontalHeaderLabels(["ID", "Patente"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addLayout(form_layout)
        layout.addWidget(self.tabla)

        self.setLayout(layout)
        self.cargar_mensuales()

    def cargar_mensuales(self):
        datos = obtener_mensuales()
        self.tabla.setRowCount(len(datos))

        for i, row in enumerate(datos):
            self.tabla.setItem(i, 0, QTableWidgetItem(str(row["id_vehiculo"])))
            self.tabla.setItem(i, 1, QTableWidgetItem(row["patente"]))

    def agregar_mensual(self):
        patente = self.patente_input.text().strip().upper()
        if not patente:
            QMessageBox.warning(self, "Atención", "Debes ingresar una patente.")
            return

        exito = agregar_mensual(patente)
        if exito:
            QMessageBox.information(self, "Éxito", f"Cliente mensual {patente} agregado.")
            self.patente_input.clear()
            self.cargar_mensuales()
        else:
            QMessageBox.critical(self, "Error", "No se pudo registrar o ya existe.")
