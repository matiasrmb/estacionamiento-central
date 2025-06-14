from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from datetime import datetime
from controllers.registro_controller import buscar_estado_vehiculo, registrar_ingreso, registrar_salida

class RegistroWindow(QWidget):
    def __init__(self, usuario):
        super().__init__()
        self.usuario = usuario
        self.setWindowTitle("Registro de Vehículos")
        self.setFixedSize(400, 250)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.label_patente = QLabel("Patente del vehículo:")
        self.input_patente = QLineEdit()

        self.boton_buscar = QPushButton("Buscar")
        self.boton_buscar.clicked.connect(self.buscar_vehiculo)

        self.info_label = QLabel("")
        self.boton_ingreso = QPushButton("Registrar Ingreso")
        self.boton_ingreso.setEnabled(False)
        self.boton_ingreso.clicked.connect(self.registrar_ingreso)

        self.boton_salida = QPushButton("Registrar Salida")
        self.boton_salida.setEnabled(False)
        self.boton_salida.clicked.connect(self.registrar_salida)

        layout.addWidget(self.label_patente)
        layout.addWidget(self.input_patente)
        layout.addWidget(self.boton_buscar)
        layout.addWidget(self.info_label)
        layout.addWidget(self.boton_ingreso)
        layout.addWidget(self.boton_salida)

        self.setLayout(layout)

    def buscar_vehiculo(self):
        patente = self.input_patente.text().strip().upper()
        if not patente:
            QMessageBox.warning(self, "Atención", "Ingresa una patente.")
            return

        estado = buscar_estado_vehiculo(patente)
        self.info_label.setText("")

        if estado == "no_registrado":
            self.info_label.setText("Vehículo no registrado. Se creará al ingresar.")
            self.boton_ingreso.setEnabled(True)
            self.boton_salida.setEnabled(False)
        elif estado == "dentro":
            self.info_label.setText("Vehículo actualmente en el estacionamiento.")
            self.boton_salida.setEnabled(True)
            self.boton_ingreso.setEnabled(False)
        elif estado == "fuera":
            self.info_label.setText("Vehículo ya salió. Puedes registrar nuevo ingreso.")
            self.boton_ingreso.setEnabled(True)
            self.boton_salida.setEnabled(False)
        else:
            QMessageBox.critical(self, "Error", "Error al consultar la patente.")

    def registrar_ingreso(self):
        patente = self.input_patente.text().strip().upper()
        exito = registrar_ingreso(patente)
        if exito:
            QMessageBox.information(self, "Éxito", f"Ingreso registrado para {patente}")
            self.reset()
        else:
            QMessageBox.critical(self, "Error", "No se pudo registrar el ingreso.")

    def registrar_salida(self):
        patente = self.input_patente.text().strip().upper()
        tarifa = registrar_salida(patente)
        if tarifa is not None:
            QMessageBox.information(self, "Salida registrada", f"Tarifa: ${tarifa:.0f}")
            self.reset()
        else:
            QMessageBox.critical(self, "Error", "No se pudo registrar la salida.")

    def reset(self):
        self.input_patente.clear()
        self.boton_ingreso.setEnabled(False)
        self.boton_salida.setEnabled(False)
        self.info_label.setText("")