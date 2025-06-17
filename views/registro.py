from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QGroupBox, QHeaderView
)
from PySide6.QtCore import QTimer, Qt
from datetime import datetime
from controllers.registro_controller import buscar_estado_vehiculo, registrar_ingreso, registrar_salida, obtener_vehiculos_activos, marcar_en_espera
from views.dashboard import DashboardWindow
from functools import partial

class RegistroWindow(QWidget):
    def __init__(self, usuario, rol="operador"):
        super().__init__()
        self.usuario = usuario
        self.rol = rol
        self.setWindowTitle("Registro de Vehículos")
        self.setMinimumSize(400, 250)
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

        # Botón para ver el resumen
        self.boton_resumen = QPushButton("Ver Resumen Diario")
        self.boton_resumen.clicked.connect(self.abrir_dashboard)
        layout.addWidget(self.boton_resumen)

        # Grupo desplegable para la tabla
        self.grupo_tabla = QGroupBox("🚗 Vehículos actualmente estacionados")
        self.grupo_tabla.setCheckable(True)
        self.grupo_tabla.setChecked(False)  # Empieza colapsado
        self.grupo_tabla.toggled.connect(self.mostrar_ocultar_tabla)

        self.tabla_activos = QTableWidget()
        self.tabla_activos.setColumnCount(4)
        self.tabla_activos.setHorizontalHeaderLabels(["Patente", "Hora Ingreso", "Monto Actual", "Acción"])
        self.tabla_activos.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tabla_activos.setMaximumHeight(200)

        layout_tabla = QVBoxLayout()
        layout_tabla.addWidget(self.tabla_activos)
        self.grupo_tabla.setLayout(layout_tabla)

        layout.addWidget(self.grupo_tabla)

        # Timer para actualizar tabla
        self.timer_tabla = QTimer()
        self.timer_tabla.timeout.connect(self.actualizar_tabla_activos)
        self.timer_tabla.start(60000)
        self.actualizar_tabla_activos()

        self.tabla_activos.horizontalHeader().setStretchLastSection(True)
        self.tabla_activos.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla_activos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla_activos.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabla_activos.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

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
        self.actualizar_tabla_activos()


    def registrar_salida(self):
        patente = self.input_patente.text().strip().upper()
        tarifa = registrar_salida(patente)
        if tarifa is not None:
            QMessageBox.information(self, "Salida registrada", f"Tarifa: ${tarifa:.0f}")
            self.reset()
        else:
            QMessageBox.critical(self, "Error", "No se pudo registrar la salida.")
        self.actualizar_tabla_activos()


    def reset(self):
        self.input_patente.clear()
        self.boton_ingreso.setEnabled(False)
        self.boton_salida.setEnabled(False)
        self.info_label.setText("")

    def abrir_dashboard(self):
        self.dashboard = DashboardWindow(self.usuario, rol="operador")  # o self.rol si lo tienes
        self.dashboard.show()

    def actualizar_tabla_activos(self):
        datos = obtener_vehiculos_activos()
        self.tabla_activos.setRowCount(len(datos) + 1)  # +1 para la fila de total
        total = 0

        for i, vehiculo in enumerate(datos):
            patente = vehiculo["patente"]
            hora = vehiculo["hora"]
            monto = vehiculo["monto"]
            en_espera = vehiculo.get("en_espera", False)

            # Columna 0: Patente
            item_patente = QTableWidgetItem(patente)
            item_patente.setFlags(item_patente.flags() ^ Qt.ItemIsEditable)
            if en_espera:
                item_patente.setForeground(Qt.gray)
            self.tabla_activos.setItem(i, 0, item_patente)

            # Columna 1: Hora ingreso
            item_hora = QTableWidgetItem(hora)
            item_hora.setFlags(item_hora.flags() ^ Qt.ItemIsEditable)
            if en_espera:
                item_hora.setForeground(Qt.gray)
            self.tabla_activos.setItem(i, 1, item_hora)

            # Columna 2: Monto
            item_monto = QTableWidgetItem(f"${monto:.0f}")
            item_monto.setFlags(item_monto.flags() ^ Qt.ItemIsEditable)
            if en_espera:
                item_monto.setForeground(Qt.gray)
            self.tabla_activos.setItem(i, 2, item_monto)

            # Sumar solo si no está en espera
            if not en_espera:
                total += monto

            # Columna 3: Botón "En espera" si corresponde
            if not en_espera:
                btn_espera = QPushButton("🕒 En espera")
                btn_espera.clicked.connect(partial(self.marcar_patente_en_espera, patente))
                self.tabla_activos.setCellWidget(i, 3, btn_espera)
            else:
                item_accion = QTableWidgetItem("")
                item_accion.setFlags(item_accion.flags() ^ Qt.ItemIsEditable)
                self.tabla_activos.setItem(i, 3, item_accion)

        # Fila final: TOTAL
        fila_total = len(datos)
        item_total_label = QTableWidgetItem("TOTAL RECAUDADO:")
        item_total_label.setFlags(item_total_label.flags() ^ Qt.ItemIsEditable)
        item_total_label.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.tabla_activos.setItem(fila_total, 1, item_total_label)

        item_total_monto = QTableWidgetItem(f"${total:.0f}")
        item_total_monto.setFlags(item_total_monto.flags() ^ Qt.ItemIsEditable)
        item_total_monto.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.tabla_activos.setItem(fila_total, 2, item_total_monto)

        # Última celda de acción vacía
        self.tabla_activos.setItem(fila_total, 3, QTableWidgetItem(""))


    def mostrar_ocultar_tabla(self, visible):
        self.tabla_activos.setVisible(visible)

    def marcar_patente_en_espera(self, patente):
        confirmar = QMessageBox.question(
            self,
            "Confirmar acción",
            f"¿Seguro que quieres marcar la patente '{patente}' como EN ESPERA?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirmar == QMessageBox.Yes:
            marcar_en_espera(patente)
            self.actualizar_tabla_activos()

