from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QDateEdit,
    QMessageBox, QFrame, QGridLayout, QSizePolicy,
    QComboBox, QTimeEdit
)
from PySide6.QtCore import QDate, QTime, Qt

from controllers.reportes_controller import obtener_reportes, exportar_pdf
from controllers.usuarios_controller import obtener_usuarios
from utils.table_filters import create_sortable_item, sort_table_from_header_click


class ReportesWindow(QWidget):
    """
    Vista para consultar y exportar reportes de ingresos y salidas
    de vehículos por rango de fechas y patente.
    """

    def __init__(self):
        super().__init__()
        self.setMinimumSize(900, 600)
        self.resultados = {"items": [], "totals": {}}
        self.ultimos_filtros = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        subtitulo = QLabel("Consulta movimientos por fecha y patente, y exporta los resultados a PDF.")
        subtitulo.setObjectName("SubtituloSeccion")
        subtitulo.setWordWrap(True)
        layout.addWidget(subtitulo)

        # =========================================================
        # FILTROS
        # =========================================================
        filtros_group = QFrame()
        filtros_group.setObjectName("PanelFormulario")
        filtros_layout_wrapper = QVBoxLayout(filtros_group)
        filtros_layout_wrapper.setContentsMargins(14, 14, 14, 14)
        filtros_layout_wrapper.setSpacing(10)

        filtros_layout = QGridLayout()
        filtros_layout.setHorizontalSpacing(12)
        filtros_layout.setVerticalSpacing(10)

        label_desde = QLabel("Desde")
        label_desde.setObjectName("EtiquetaFormulario")
        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setDate(QDate.currentDate())
        self.fecha_inicio.setCalendarPopup(True)
        self.fecha_inicio.setMinimumHeight(38)

        label_hasta = QLabel("Hasta")
        label_hasta.setObjectName("EtiquetaFormulario")
        self.fecha_fin = QDateEdit()
        self.fecha_fin.setDate(QDate.currentDate())
        self.fecha_fin.setCalendarPopup(True)
        self.fecha_fin.setMinimumHeight(38)

        label_hora_inicio = QLabel("Hora desde")
        label_hora_inicio.setObjectName("EtiquetaFormulario")
        self.hora_inicio = QTimeEdit()
        self.hora_inicio.setDisplayFormat("HH:mm")
        self.hora_inicio.setTime(QTime(0, 0))
        self.hora_inicio.setMinimumHeight(38)

        label_hora_fin = QLabel("Hora hasta")
        label_hora_fin.setObjectName("EtiquetaFormulario")
        self.hora_fin = QTimeEdit()
        self.hora_fin.setDisplayFormat("HH:mm")
        self.hora_fin.setTime(QTime(23, 59))
        self.hora_fin.setMinimumHeight(38)

        label_patente = QLabel("Patente")
        label_patente.setObjectName("EtiquetaFormulario")
        self.input_patente = QLineEdit()
        self.input_patente.setPlaceholderText("Opcional")
        self.input_patente.setMinimumHeight(38)
        self.input_patente.returnPressed.connect(self.filtrar)

        label_usuario = QLabel("Usuario")
        label_usuario.setObjectName("EtiquetaFormulario")
        self.combo_usuario = QComboBox()
        self.combo_usuario.setMinimumHeight(38)
        self.cargar_usuarios()

        self.boton_filtrar = QPushButton("Buscar")
        self.boton_filtrar.setMinimumHeight(40)
        self.boton_filtrar.clicked.connect(self.filtrar)

        self.boton_limpiar = QPushButton("Limpiar filtros")
        self.boton_limpiar.setObjectName("BotonSecundario")
        self.boton_limpiar.setMinimumHeight(38)
        self.boton_limpiar.clicked.connect(self.limpiar_filtros)

        self.boton_actualizar = QPushButton("Actualizar")
        self.boton_actualizar.setObjectName("BotonSecundario")
        self.boton_actualizar.setMinimumHeight(38)
        self.boton_actualizar.clicked.connect(self.filtrar)

        self.boton_exportar = QPushButton("Exportar PDF")
        self.boton_exportar.setMinimumHeight(40)
        self.boton_exportar.setEnabled(False)
        self.boton_exportar.clicked.connect(self.exportar_pdf)

        filtros_layout.addWidget(label_desde, 0, 0)
        filtros_layout.addWidget(self.fecha_inicio, 0, 1)
        filtros_layout.addWidget(label_hasta, 0, 2)
        filtros_layout.addWidget(self.fecha_fin, 0, 3)
        filtros_layout.addWidget(label_patente, 0, 4)
        filtros_layout.addWidget(self.input_patente, 0, 5)
        filtros_layout.addWidget(self.boton_filtrar, 0, 6)

        filtros_layout.addWidget(label_hora_inicio, 1, 0)
        filtros_layout.addWidget(self.hora_inicio, 1, 1)
        filtros_layout.addWidget(label_hora_fin, 1, 2)
        filtros_layout.addWidget(self.hora_fin, 1, 3)

        filtros_layout.addWidget(label_usuario, 2, 0)
        filtros_layout.addWidget(self.combo_usuario, 2, 1)
        filtros_layout.addWidget(self.boton_limpiar, 1, 4)
        filtros_layout.addWidget(self.boton_actualizar, 1, 5)
        filtros_layout.addWidget(self.boton_exportar, 1, 6)

        filtros_layout.setColumnStretch(1, 1)
        filtros_layout.setColumnStretch(3, 1)
        filtros_layout.setColumnStretch(5, 1)

        filtros_layout_wrapper.addLayout(filtros_layout)
        layout.addWidget(filtros_group)

        # =========================================================
        # RESUMEN
        # =========================================================
        resumen_layout = QHBoxLayout()
        resumen_layout.setSpacing(12)

        self.card_movimientos = self.crear_tarjeta_resumen("Movimientos encontrados", "0")
        self.card_total = self.crear_tarjeta_resumen("Total bruto", "$0")
        self.card_gastos = self.crear_tarjeta_resumen("Gastos", "$0")
        self.card_neto = self.crear_tarjeta_resumen("Total neto", "$0")

        resumen_layout.addWidget(self.card_movimientos)
        resumen_layout.addWidget(self.card_total)
        resumen_layout.addWidget(self.card_gastos)
        resumen_layout.addWidget(self.card_neto)
        resumen_layout.addStretch()

        layout.addLayout(resumen_layout)

        # =========================================================
        # TABLA
        # =========================================================
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels(["Categoría", "Patente", "Ingreso", "Salida", "Minutos", "Usuario", "Monto"])
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tabla.verticalHeader().setDefaultSectionSize(38)

        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().sectionClicked.connect(self.ordenar_tabla)

        layout.addWidget(self.tabla, 1)

        self.setLayout(layout)

    def cargar_usuarios(self):
        self.combo_usuario.clear()
        self.combo_usuario.addItem("Todos", "")
        try:
            for usuario in obtener_usuarios():
                nombre = usuario.get("usuario")
                if nombre:
                    self.combo_usuario.addItem(nombre, nombre)
        except Exception:
            pass

    def crear_tarjeta_resumen(self, titulo, valor):
        frame = QFrame()
        frame.setObjectName("ResumenModulo")
        frame.setMinimumHeight(86)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(14, 12, 14, 12)
        frame_layout.setSpacing(4)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("TituloResumenModulo")
        label_titulo.setWordWrap(True)

        label_valor = QLabel(valor)
        label_valor.setObjectName("ValorResumenModulo")
        label_valor.setWordWrap(True)

        frame_layout.addWidget(label_titulo)
        frame_layout.addWidget(label_valor)

        frame.label_valor = label_valor
        return frame

    def limpiar_filtros(self):
        self.fecha_inicio.setDate(QDate.currentDate())
        self.fecha_fin.setDate(QDate.currentDate())
        self.hora_inicio.setTime(QTime(0, 0))
        self.hora_fin.setTime(QTime(23, 59))
        self.input_patente.clear()
        self.combo_usuario.setCurrentIndex(0)
        self.resultados = {"items": [], "totals": {}}
        self.tabla.setRowCount(0)
        self.card_movimientos.label_valor.setText("0")
        self.card_total.label_valor.setText("$0")
        self.card_gastos.label_valor.setText("$0")
        self.card_neto.label_valor.setText("$0")
        self.boton_exportar.setEnabled(False)

    def filtrar(self):
        fecha_inicio = self.fecha_inicio.date().toPython()
        fecha_fin = self.fecha_fin.date().toPython()
        patente = self.input_patente.text().strip().upper()
        hora_inicio = self.hora_inicio.time().toPython()
        hora_fin = self.hora_fin.time().toPython()
        usuario = self.combo_usuario.currentData() or ""

        self.resultados = obtener_reportes(fecha_inicio, fecha_fin, patente, hora_inicio, hora_fin, usuario)
        items = self.resultados.get("items", [])
        totals = self.resultados.get("totals", {})
        self.ultimos_filtros = {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "patente": patente,
            "hora_inicio": hora_inicio,
            "hora_fin": hora_fin,
            "usuario": usuario,
        }

        if not items:
            self.tabla.setRowCount(0)
            self.card_movimientos.label_valor.setText("0")
            self.card_total.label_valor.setText("$0")
            self.card_gastos.label_valor.setText("$0")
            self.card_neto.label_valor.setText("$0")
            self.boton_exportar.setEnabled(False)
            QMessageBox.information(self, "Sin resultados", "No se encontraron movimientos en ese rango.")
            return

        self.tabla.setRowCount(len(items) + 1)
        self.tabla.setSortingEnabled(False)

        for i, row in enumerate(items):
            ingreso = row["fecha_hora_ingreso"].strftime("%d-%m-%Y %H:%M")
            salida = row["fecha_hora_salida"].strftime("%d-%m-%Y %H:%M")
            tarifa = row["tarifa_aplicada"]
            categoria = row.get("categoria", "")
            usuario_row = row.get("usuario") or "-"

            item_categoria = create_sortable_item(categoria)
            item_patente = create_sortable_item(row["patente"])
            item_ingreso = create_sortable_item(ingreso, sort_value=row["fecha_hora_ingreso"])
            item_salida = create_sortable_item(salida, sort_value=row["fecha_hora_salida"])
            item_minutos = create_sortable_item(str(row["minutos"]), sort_value=row["minutos"])
            item_usuario = create_sortable_item(usuario_row)
            item_monto = create_sortable_item(f"${tarifa:.0f}", sort_value=tarifa)

            item_patente.setTextAlignment(Qt.AlignCenter)
            item_minutos.setTextAlignment(Qt.AlignCenter)
            item_monto.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.tabla.setItem(i, 0, item_categoria)
            self.tabla.setItem(i, 1, item_patente)
            self.tabla.setItem(i, 2, item_ingreso)
            self.tabla.setItem(i, 3, item_salida)
            self.tabla.setItem(i, 4, item_minutos)
            self.tabla.setItem(i, 5, item_usuario)
            self.tabla.setItem(i, 6, item_monto)

        fila_total = len(items)

        for columna in range(5):
            self.tabla.setItem(fila_total, columna, QTableWidgetItem(""))

        item_total_label = QTableWidgetItem("TOTAL NETO:")
        item_total_label.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

        item_total_valor = QTableWidgetItem(f"${totals.get('total_neto', 0):.0f}")
        item_total_valor.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.tabla.setItem(fila_total, 5, item_total_label)
        self.tabla.setItem(fila_total, 6, item_total_valor)

        for col in range(self.tabla.columnCount()):
            item = self.tabla.item(fila_total, col)
            if item:
                fuente = item.font()
                fuente.setBold(True)
                item.setFont(fuente)

        self.card_movimientos.label_valor.setText(str(totals.get("total_movimientos", len(items))))
        self.card_total.label_valor.setText(f"${totals.get('total_general', 0):.0f}")
        self.card_gastos.label_valor.setText(f"${totals.get('total_gastos', 0):.0f}")
        self.card_neto.label_valor.setText(f"${totals.get('total_neto', 0):.0f}")
        self.boton_exportar.setEnabled(True)

    def ordenar_tabla(self, columna):
        if self.tabla.rowCount() == 0:
            return
        sort_table_from_header_click(
            self.tabla,
            columna,
            protected_rows={self.tabla.rowCount() - 1},
        )

    def exportar_pdf(self):
        if self.resultados.get("items"):
            filtros = self.ultimos_filtros or {}
            fecha_inicio = filtros.get("fecha_inicio")
            fecha_fin = filtros.get("fecha_fin")
            patente = filtros.get("patente", "")
            exportar_pdf(
                self.resultados,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                incluir_banos=not bool(patente),
                patente=patente,
            )
        else:
            QMessageBox.information(self, "Aviso", "Primero realiza una búsqueda para poder exportar.")
