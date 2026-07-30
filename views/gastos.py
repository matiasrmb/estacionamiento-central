from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget, QHeaderView,
)

from controllers.gastos_controller import (
    obtener_gastos_pendientes,
    obtener_total_gastos_pendientes,
    registrar_gasto,
)


class GastosWindow(QWidget):
    """Registro y consulta de gastos pendientes del cierre actual."""

    CATEGORIAS = ("Insumos", "Mantención", "Servicios", "Otros")

    def __init__(self, usuario):
        super().__init__()
        self.usuario = usuario
        self.init_ui()
        self.cargar_gastos()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        descripcion = QLabel("Registra gastos operacionales pendientes del cierre actual.")
        descripcion.setObjectName("SubtituloSeccion")
        descripcion.setWordWrap(True)
        layout.addWidget(descripcion)

        formulario = QFrame()
        formulario.setObjectName("PanelFormulario")
        campos = QFormLayout(formulario)
        campos.setContentsMargins(14, 14, 14, 14)
        campos.setSpacing(10)

        self.categoria = QComboBox()
        self.categoria.addItems(self.CATEGORIAS)
        self.categoria.setMinimumHeight(38)
        self.descripcion = QLineEdit()
        self.descripcion.setPlaceholderText("Detalle del gasto")
        self.descripcion.setMinimumHeight(38)
        self.monto = QLineEdit()
        self.monto.setPlaceholderText("Monto en CLP")
        self.monto.setMinimumHeight(38)
        self.monto.returnPressed.connect(self.registrar)
        self.btn_registrar = QPushButton("Registrar gasto")
        self.btn_registrar.setMinimumHeight(40)
        self.btn_registrar.clicked.connect(self.registrar)

        campos.addRow("Categoría", self.categoria)
        campos.addRow("Descripción", self.descripcion)
        campos.addRow("Monto", self.monto)
        campos.addRow("", self.btn_registrar)
        layout.addWidget(formulario)

        resumen = QHBoxLayout()
        resumen.addWidget(QLabel("Total de gastos pendientes:"))
        self.total = QLabel("$0")
        self.total.setObjectName("ValorResumenModulo")
        resumen.addWidget(self.total)
        resumen.addStretch()
        layout.addLayout(resumen)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Fecha", "Categoría", "Descripción", "Monto", "Usuario"])
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        for columna in (0, 1, 3, 4):
            self.tabla.horizontalHeader().setSectionResizeMode(columna, QHeaderView.ResizeToContents)
        layout.addWidget(self.tabla, 1)

    def registrar(self):
        try:
            registrar_gasto(
                self.categoria.currentText(),
                self.descripcion.text(),
                self.monto.text(),
                self.usuario,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Datos inválidos", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo registrar el gasto.\n{exc}")
            return

        self.descripcion.clear()
        self.monto.clear()
        self.cargar_gastos()

    def cargar_gastos(self):
        try:
            gastos = obtener_gastos_pendientes()
            total = obtener_total_gastos_pendientes()
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los gastos.\n{exc}")
            return

        self.tabla.setRowCount(len(gastos))
        for fila, gasto in enumerate(gastos):
            fecha = gasto["fecha_hora"].strftime("%d/%m/%Y %H:%M")
            valores = (fecha, gasto["categoria"], gasto["descripcion"], f"${int(gasto['monto']):,}", gasto["usuario"])
            for columna, valor in enumerate(valores):
                item = QTableWidgetItem(str(valor))
                if columna == 3:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla.setItem(fila, columna, item)
        self.total.setText(f"${total:,}")
