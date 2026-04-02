from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QHBoxLayout,
    QInputDialog, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt
from functools import partial

from controllers.mensuales_controller import (
    obtener_mensuales, agregar_mensual,
    actualizar_tarifa, eliminar_mensual
)


class MensualesWindow(QWidget):
    """
    Vista para la gestión de clientes con plan mensual.
    Permite registrar patentes, editar tarifas y eliminar clientes.
    """

    def __init__(self):
        super().__init__()
        self.setMinimumSize(900, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        subtitulo = QLabel("Administra patentes con plan mensual y sus tarifas asociadas.")
        subtitulo.setObjectName("SubtituloSeccion")
        subtitulo.setWordWrap(True)
        layout.addWidget(subtitulo)

        # =========================================================
        # FORMULARIO
        # =========================================================
        formulario = QFrame()
        formulario.setObjectName("PanelFormulario")
        form_wrapper = QVBoxLayout(formulario)
        form_wrapper.setContentsMargins(14, 14, 14, 14)
        form_wrapper.setSpacing(10)

        label_form = QLabel("Agregar nuevo cliente mensual")
        label_form.setObjectName("EtiquetaFormulario")
        form_wrapper.addWidget(label_form)

        form_layout = QHBoxLayout()
        form_layout.setSpacing(10)

        self.patente_input = QLineEdit()
        self.patente_input.setPlaceholderText("Ej: ABCD12")
        self.patente_input.setMinimumHeight(38)
        self.patente_input.returnPressed.connect(self.agregar_mensual)

        self.btn_agregar = QPushButton("Agregar")
        self.btn_agregar.setMinimumHeight(38)
        self.btn_agregar.clicked.connect(self.agregar_mensual)

        form_layout.addWidget(self.patente_input, 3)
        form_layout.addWidget(self.btn_agregar, 1)

        form_wrapper.addLayout(form_layout)
        layout.addWidget(formulario)

        # =========================================================
        # TABLA
        # =========================================================
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["ID", "Patente", "Tarifa Mensual", "Acciones"])
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tabla.verticalHeader().setDefaultSectionSize(58)

        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        layout.addWidget(self.tabla, 1)

        self.setLayout(layout)
        self.cargar_mensuales()

    def cargar_mensuales(self):
        self.tabla.setRowCount(0)
        datos = obtener_mensuales()

        for i, row in enumerate(datos):
            self.tabla.insertRow(i)

            item_id = QTableWidgetItem(str(row["id_vehiculo"]))
            item_patente = QTableWidgetItem(row["patente"])
            item_tarifa = QTableWidgetItem(str(row.get("tarifa_mensual") or "0"))

            item_id.setTextAlignment(Qt.AlignCenter)
            item_patente.setTextAlignment(Qt.AlignCenter)
            item_tarifa.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.tabla.setItem(i, 0, item_id)
            self.tabla.setItem(i, 1, item_patente)
            self.tabla.setItem(i, 2, item_tarifa)

            btn_tarifa = QPushButton("Editar tarifa")
            btn_tarifa.setObjectName("BotonTabla")
            btn_tarifa.setMinimumHeight(34)
            btn_tarifa.clicked.connect(partial(self.editar_tarifa, row["id_vehiculo"]))

            btn_eliminar = QPushButton("Eliminar")
            btn_eliminar.setObjectName("BotonTablaPeligro")
            btn_eliminar.setMinimumHeight(34)
            btn_eliminar.clicked.connect(partial(self.eliminar_cliente, row["id_vehiculo"]))

            acciones_layout = QHBoxLayout()
            acciones_layout.setContentsMargins(6, 4, 6, 4)
            acciones_layout.setSpacing(6)
            acciones_layout.addWidget(btn_tarifa)
            acciones_layout.addWidget(btn_eliminar)

            acciones_widget = QWidget()
            acciones_widget.setLayout(acciones_layout)

            self.tabla.setCellWidget(i, 3, acciones_widget)

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
        nueva_tarifa, ok = QInputDialog.getDouble(
            self,
            "Editar tarifa",
            "Ingresa nueva tarifa mensual:",
            decimals=0
        )
        if ok:
            actualizar_tarifa(id_vehiculo, nueva_tarifa)
            self.cargar_mensuales()