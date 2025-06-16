from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QHBoxLayout, QInputDialog
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
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["ID", "Patente", "Tarifa Mensual", "Acciones"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addLayout(form_layout)
        layout.addWidget(self.tabla)

        self.setLayout(layout)
        self.cargar_mensuales()

    def cargar_mensuales(self):
        from functools import partial
        datos = obtener_mensuales()
        self.tabla.setRowCount(len(datos))

        for i, row in enumerate(datos):
            self.tabla.setItem(i, 0, QTableWidgetItem(str(row["id_vehiculo"])))
            self.tabla.setItem(i, 1, QTableWidgetItem(row["patente"]))
            self.tabla.setItem(i, 2, QTableWidgetItem(str(row.get("tarifa_mensual") or "0")))

            btn_eliminar = QPushButton("Eliminar")
            btn_eliminar.clicked.connect(partial(self.eliminar_cliente, row["id_vehiculo"]))

            btn_tarifa = QPushButton("Editar Tarifa")
            btn_tarifa.clicked.connect(partial(self.editar_tarifa, row["id_vehiculo"]))

            actions = QWidget()
            action_layout = QHBoxLayout()
            action_layout.addWidget(btn_eliminar)
            action_layout.addWidget(btn_tarifa)
            action_layout.setContentsMargins(0, 0, 0, 0)
            actions.setLayout(action_layout)

            self.tabla.setCellWidget(i, 3, actions)

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

    def eliminar_cliente(self, id_vehiculo):
        from controllers.mensuales_controller import eliminar_mensual
        confirm = QMessageBox.question(self, "Confirmar",
            "¿Seguro que deseas eliminar este cliente mensual?",
            QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            eliminar_mensual(id_vehiculo)
            self.cargar_mensuales()

    def editar_tarifa(self, id_vehiculo):
        from controllers.mensuales_controller import actualizar_tarifa
        nueva_tarifa, ok = QInputDialog.getDouble(
            self,
            "Editar Tarifa",
            "Ingresa nueva tarifa mensual:",
            decimals=0
        )
        if ok:
            actualizar_tarifa(id_vehiculo, nueva_tarifa)
            self.cargar_mensuales()
