from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QHBoxLayout,
    QSizePolicy, QFrame, QFormLayout, QSpinBox, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt
from functools import partial

from controllers.mensuales_controller import (
    obtener_mensuales, agregar_mensual,
    actualizar_tarifa, eliminar_mensual, registrar_pago_mensual
)
from utils.plates import normalizar_patente, validar_patente
from utils.table_filters import filtrar_filas_tabla


class MensualesWindow(QWidget):
    """
    Vista para la gestión de clientes con plan mensual.
    Permite registrar patentes, editar tarifas y eliminar clientes.
    """

    def __init__(self, usuario=None):
        super().__init__()
        self.usuario = usuario or "sistema"
        self.setMinimumSize(900, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        subtitulo = QLabel("Administra clientes mensuales, su vencimiento, teléfono y pagos.")
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

        self.tarifa_input = QSpinBox()
        self.tarifa_input.setRange(1, 99999999)
        self.tarifa_input.setValue(1)
        self.tarifa_input.setPrefix("$ ")
        self.tarifa_input.setMinimumHeight(38)

        self.vencimiento_input = QSpinBox()
        self.vencimiento_input.setRange(1, 31)
        self.vencimiento_input.setValue(1)
        self.vencimiento_input.setPrefix("Día ")
        self.vencimiento_input.setMinimumHeight(38)

        self.telefono_input = QLineEdit()
        self.telefono_input.setPlaceholderText("Teléfono")
        self.telefono_input.setMinimumHeight(38)
        self.telefono_input.returnPressed.connect(self.agregar_mensual)

        self.btn_agregar = QPushButton("Agregar")
        self.btn_agregar.setMinimumHeight(38)
        self.btn_agregar.clicked.connect(self.agregar_mensual)

        self.btn_actualizar = QPushButton("Actualizar")
        self.btn_actualizar.setObjectName("BotonSecundario")
        self.btn_actualizar.setMinimumHeight(38)
        self.btn_actualizar.clicked.connect(self.cargar_mensuales)

        form_layout.addWidget(self.patente_input, 3)
        form_layout.addWidget(self.tarifa_input, 2)
        form_layout.addWidget(self.vencimiento_input, 1)
        form_layout.addWidget(self.telefono_input, 2)
        form_layout.addWidget(self.btn_agregar, 1)
        form_layout.addWidget(self.btn_actualizar, 1)

        form_wrapper.addLayout(form_layout)
        layout.addWidget(formulario)

        # =========================================================
        # TABLA
        # =========================================================
        self.busqueda = QLineEdit()
        self.busqueda.setPlaceholderText("Buscar...")
        self.busqueda.setMinimumHeight(38)
        self.busqueda.textChanged.connect(self.filtrar_tabla)
        layout.addWidget(self.busqueda)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Patente", "Teléfono", "Tarifa mensual", "Vencimiento", "Estado", "Pago", "Acciones"
        ])
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tabla.verticalHeader().setDefaultSectionSize(58)

        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)

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
            item_telefono = QTableWidgetItem(row.get("telefono") or "-")
            item_tarifa = QTableWidgetItem(str(row.get("tarifa_mensual") or "0"))
            item_vencimiento = QTableWidgetItem(f"Día {row.get('dia_vencimiento') or 1}")
            estado = row.get("estado_pago") or "pendiente"
            item_estado = QTableWidgetItem(estado.capitalize())
            fecha_pago = row.get("fecha_pago")
            pago_texto = fecha_pago.strftime("%d/%m/%Y") if hasattr(fecha_pago, "strftime") else str(fecha_pago or "Sin pago")
            item_pago = QTableWidgetItem(pago_texto)

            item_id.setTextAlignment(Qt.AlignCenter)
            item_patente.setTextAlignment(Qt.AlignCenter)
            item_telefono.setTextAlignment(Qt.AlignCenter)
            item_tarifa.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_vencimiento.setTextAlignment(Qt.AlignCenter)
            item_estado.setTextAlignment(Qt.AlignCenter)
            item_pago.setTextAlignment(Qt.AlignCenter)

            self.tabla.setItem(i, 0, item_id)
            self.tabla.setItem(i, 1, item_patente)
            self.tabla.setItem(i, 2, item_telefono)
            self.tabla.setItem(i, 3, item_tarifa)
            self.tabla.setItem(i, 4, item_vencimiento)
            self.tabla.setItem(i, 5, item_estado)
            self.tabla.setItem(i, 6, item_pago)

            btn_tarifa = QPushButton("Editar")
            btn_tarifa.setObjectName("BotonTabla")
            btn_tarifa.setMinimumHeight(34)
            btn_tarifa.clicked.connect(partial(self.editar_tarifa, row))

            btn_pago = QPushButton("Registrar pago")
            btn_pago.setObjectName("BotonTabla")
            btn_pago.setMinimumHeight(34)
            btn_pago.setEnabled(estado != "pagado")
            btn_pago.clicked.connect(partial(self.registrar_pago, row["id_vehiculo"], row["patente"]))

            btn_eliminar = QPushButton("Eliminar")
            btn_eliminar.setObjectName("BotonTablaPeligro")
            btn_eliminar.setMinimumHeight(34)
            btn_eliminar.clicked.connect(partial(self.eliminar_cliente, row["id_vehiculo"]))

            acciones_layout = QHBoxLayout()
            acciones_layout.setContentsMargins(6, 4, 6, 4)
            acciones_layout.setSpacing(6)
            acciones_layout.addWidget(btn_tarifa)
            acciones_layout.addWidget(btn_pago)
            acciones_layout.addWidget(btn_eliminar)

            acciones_widget = QWidget()
            acciones_widget.setLayout(acciones_layout)

            self.tabla.setCellWidget(i, 7, acciones_widget)

        self.filtrar_tabla()

    def filtrar_tabla(self):
        filtrar_filas_tabla(self.tabla, self.busqueda.text())

    def agregar_mensual(self):
        patente = normalizar_patente(self.patente_input.text())
        tarifa_mensual = self.tarifa_input.value()
        dia_vencimiento = self.vencimiento_input.value()
        telefono = self.telefono_input.text().strip()
        if not validar_patente(patente):
            QMessageBox.warning(
                self,
                "Atención",
                "Patente inválida. Usa ABCD12, ABC12, AB123CD o ABC123.",
            )
            return

        exito = agregar_mensual(patente, tarifa_mensual, dia_vencimiento, telefono)
        if exito:
            QMessageBox.information(self, "Éxito", f"Cliente mensual {patente} agregado.")
            self.patente_input.clear()
            self.tarifa_input.setValue(1)
            self.vencimiento_input.setValue(1)
            self.telefono_input.clear()
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

    def editar_tarifa(self, row):
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar cliente mensual")
        layout = QFormLayout(dialog)

        tarifa = QSpinBox(dialog)
        tarifa.setRange(1, 99999999)
        tarifa.setValue(int(row.get("tarifa_mensual") or 1))
        tarifa.setPrefix("$ ")
        vencimiento = QSpinBox(dialog)
        vencimiento.setRange(1, 31)
        vencimiento.setValue(int(row.get("dia_vencimiento") or 1))
        telefono = QLineEdit(row.get("telefono") or "", dialog)

        layout.addRow("Tarifa mensual:", tarifa)
        layout.addRow("Día de vencimiento:", vencimiento)
        layout.addRow("Teléfono:", telefono)
        botones = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, dialog)
        botones.accepted.connect(dialog.accept)
        botones.rejected.connect(dialog.reject)
        layout.addRow(botones)

        if dialog.exec() == QDialog.Accepted:
            actualizar_tarifa(row["id_vehiculo"], tarifa.value(), vencimiento.value(), telefono.text().strip())
            self.cargar_mensuales()

    def registrar_pago(self, id_vehiculo, patente):
        confirm = QMessageBox.question(
            self,
            "Confirmar pago",
            f"¿Confirmas que recibiste el pago mensual de {patente}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        exito, mensaje = registrar_pago_mensual(id_vehiculo, self.usuario)
        if exito:
            QMessageBox.information(self, "Pago registrado", mensaje)
            self.cargar_mensuales()
        else:
            QMessageBox.warning(self, "No se registró el pago", mensaje)
