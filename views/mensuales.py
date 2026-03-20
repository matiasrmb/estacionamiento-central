from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QHBoxLayout,
    QInputDialog, QGroupBox
)
from PySide6.QtCore import Qt
from functools import partial

from controllers.mensuales_controller import (
    obtener_mensuales, agregar_mensual, 
    actualizar_tarifa, eliminar_mensual
)

class MensualesWindow(QWidget):
    """
    Ventana para la gestión de clientes con plan mensual.
    Permite registrar patentes, editar tarifas y eliminar clientes.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clientes Mensuales")
        self.setMinimumSize(900, 600) 
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Encabezado
        self.label_titulo = QLabel("📘 Gestión de Clientes Mensuales")
        self.label_titulo.setObjectName("TituloVentana")
        self.label_titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_titulo)

        # Formulario de ingreso
        form_group = QGroupBox("➕ Agregar nuevo cliente mensual")
        form_layout = QHBoxLayout()
        form_layout.setContentsMargins(10, 20, 10, 20)
        form_layout.setSpacing(10)

        self.patente_input = QLineEdit()
        self.patente_input.setPlaceholderText("Ej: ABCD12")
        self.patente_input.setMinimumHeight(38)

        self.btn_agregar = QPushButton("Agregar")
        self.btn_agregar.clicked.connect(self.agregar_mensual)
        self.btn_agregar.setMinimumHeight(38)

        form_layout.addWidget(self.patente_input)
        form_layout.addWidget(self.btn_agregar)
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["ID", "Patente", "Tarifa Mensual", "Acciones"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Patente
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Tarifa Mensual
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Acciones
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.verticalHeader().setDefaultSectionSize(40)

        layout.addWidget(self.tabla)
        self.setLayout(layout)
        self.cargar_mensuales()

    def cargar_mensuales(self):
        """Carga los clientes mensuales desde la base de datos a la tabla."""
        self.tabla.setRowCount(0)
        datos = obtener_mensuales()

        for i, row in enumerate(datos):
            self.tabla.insertRow(i)
            self.tabla.setItem(i, 0, QTableWidgetItem(str(row["id_vehiculo"])))
            self.tabla.setItem(i, 1, QTableWidgetItem(row["patente"]))
            self.tabla.setItem(i, 2, QTableWidgetItem(str(row.get("tarifa_mensual") or "0")))

            # Botones de acción
            btn_eliminar = QPushButton("🗑 Eliminar")
            btn_eliminar.clicked.connect(partial(self.eliminar_cliente, row["id_vehiculo"]))

            btn_tarifa = QPushButton("💰 Editar Tarifa")
            btn_tarifa.clicked.connect(partial(self.editar_tarifa, row["id_vehiculo"]))

            acciones_layout = QHBoxLayout()
            acciones_layout.addWidget(btn_tarifa)
            acciones_layout.addWidget(btn_eliminar)
            acciones_layout.setContentsMargins(0, 0, 0, 0)
            acciones_layout.setSpacing(5)

            acciones_widget = QWidget()
            acciones_widget.setLayout(acciones_layout)

            self.tabla.setCellWidget(i, 3, acciones_widget)

    def agregar_mensual(self):
        """Agrega una nueva patente como cliente mensual."""
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
        """Elimina un cliente mensual."""
        confirm = QMessageBox.question(
            self,
            "Confirmar eliminación",
            "¿Estás seguro de eliminar este cliente mensual?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            eliminar_mensual(id_vehiculo)
            self.cargar_mensuales()

    def editar_tarifa(self, id_vehiculo):
        """Permite editar la tarifa mensual de un cliente."""
        nueva_tarifa, ok = QInputDialog.getDouble(
            self,
            "Editar Tarifa",
            "Ingresa nueva tarifa mensual:",
            decimals=0
        )
        if ok:
            actualizar_tarifa(id_vehiculo, nueva_tarifa)
            self.cargar_mensuales()
