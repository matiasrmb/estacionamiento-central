from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QInputDialog, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QHeaderView,
)

from controllers.gastos_controller import (
    editar_gasto,
    eliminar_gasto,
    obtener_gastos_pendientes,
    obtener_total_gastos_pendientes,
    registrar_gasto,
)
from utils.table_filters import filtrar_filas_tabla


class GastosWindow(QWidget):
    """Registro y consulta de gastos pendientes del cierre actual."""

    CATEGORIAS = ("Insumos", "Mantención", "Servicios", "Otros")

    def __init__(self, usuario, rol="operador"):
        super().__init__()
        self.usuario = usuario
        self.rol = rol
        self.init_ui()
        self.cargar_gastos()

    @property
    def es_admin(self):
        return str(self.rol or "").strip().lower() in {"admin", "administrador"}

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

        self.busqueda = QLineEdit()
        self.busqueda.setPlaceholderText("Buscar...")
        self.busqueda.setMinimumHeight(38)
        self.busqueda.textChanged.connect(self.filtrar_tabla)
        layout.addWidget(self.busqueda)

        self.tabla = QTableWidget()
        columnas = ["Fecha", "Categoría", "Descripción", "Monto", "Usuario"]
        if self.es_admin:
            columnas.append("Acciones")
        self.tabla.setColumnCount(len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.verticalHeader().setDefaultSectionSize(48)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        for columna in (0, 1, 3, 4):
            self.tabla.horizontalHeader().setSectionResizeMode(columna, QHeaderView.ResizeToContents)
        if self.es_admin:
            self.tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
            self.tabla.setColumnWidth(5, 190)
        layout.addWidget(self.tabla, 1)

    def registrar(self):
        if QMessageBox.question(
            self,
            "Confirmar gasto",
            "¿Registrar este gasto operacional?",
        ) != QMessageBox.Yes:
            return
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
            if self.es_admin:
                acciones = QWidget()
                layout = QHBoxLayout(acciones)
                layout.setContentsMargins(6, 4, 6, 4)
                layout.setSpacing(6)
                btn_editar = QPushButton("Editar")
                btn_eliminar = QPushButton("Eliminar")
                for boton in (btn_editar, btn_eliminar):
                    boton.setMinimumWidth(78)
                    boton.setMinimumHeight(30)
                btn_editar.clicked.connect(lambda _checked=False, g=gasto: self.editar(g))
                btn_eliminar.clicked.connect(lambda _checked=False, g=gasto: self.eliminar(g))
                layout.addWidget(btn_editar)
                layout.addWidget(btn_eliminar)
                self.tabla.setCellWidget(fila, 5, acciones)
        self.total.setText(f"${total:,}")
        self.filtrar_tabla()

    def editar(self, gasto):
        categoria, ok = QInputDialog.getItem(self, "Editar gasto", "Categoría", self.CATEGORIAS, self.CATEGORIAS.index(gasto["categoria"]) if gasto.get("categoria") in self.CATEGORIAS else 0, False)
        if not ok:
            return
        descripcion, ok = QInputDialog.getText(self, "Editar gasto", "Descripción", text=str(gasto.get("descripcion") or ""))
        if not ok:
            return
        monto, ok = QInputDialog.getText(self, "Editar gasto", "Monto", text=str(gasto.get("monto") or ""))
        if not ok:
            return
        if QMessageBox.question(self, "Confirmar edición", "¿Guardar los cambios del gasto?") != QMessageBox.Yes:
            return
        try:
            editar_gasto(gasto["id_gasto"], categoria, descripcion, monto, self.usuario, self.rol)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo editar el gasto.\n{exc}")
            return
        self.cargar_gastos()

    def eliminar(self, gasto):
        if QMessageBox.question(self, "Confirmar eliminación", "¿Eliminar este gasto operacional?") != QMessageBox.Yes:
            return
        try:
            eliminar_gasto(gasto["id_gasto"], self.usuario, self.rol)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar el gasto.\n{exc}")
            return
        self.cargar_gastos()

    def filtrar_tabla(self):
        filtrar_filas_tabla(self.tabla, self.busqueda.text())
