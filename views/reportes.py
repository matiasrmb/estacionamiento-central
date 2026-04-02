from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QDateEdit,
    QMessageBox, QFrame, QGridLayout, QSizePolicy
)
from PySide6.QtCore import QDate, Qt

from controllers.reportes_controller import obtener_reportes, exportar_pdf


class ReportesWindow(QWidget):
    """
    Vista para consultar y exportar reportes de ingresos y salidas
    de vehículos por rango de fechas y patente.
    """

    def __init__(self):
        super().__init__()
        self.setMinimumSize(900, 600)
        self.resultados = []
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

        label_patente = QLabel("Patente")
        label_patente.setObjectName("EtiquetaFormulario")
        self.input_patente = QLineEdit()
        self.input_patente.setPlaceholderText("Opcional")
        self.input_patente.setMinimumHeight(38)
        self.input_patente.returnPressed.connect(self.filtrar)

        self.boton_filtrar = QPushButton("Buscar")
        self.boton_filtrar.setMinimumHeight(40)
        self.boton_filtrar.clicked.connect(self.filtrar)

        self.boton_limpiar = QPushButton("Limpiar filtros")
        self.boton_limpiar.setObjectName("BotonSecundario")
        self.boton_limpiar.setMinimumHeight(38)
        self.boton_limpiar.clicked.connect(self.limpiar_filtros)

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

        filtros_layout.addWidget(self.boton_limpiar, 1, 5)
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
        self.card_total = self.crear_tarjeta_resumen("Total recaudado", "$0")

        resumen_layout.addWidget(self.card_movimientos)
        resumen_layout.addWidget(self.card_total)
        resumen_layout.addStretch()

        layout.addLayout(resumen_layout)

        # =========================================================
        # TABLA
        # =========================================================
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Patente", "Ingreso", "Salida", "Minutos", "Monto"])
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tabla.verticalHeader().setDefaultSectionSize(38)

        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)

        layout.addWidget(self.tabla, 1)

        self.setLayout(layout)

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
        self.input_patente.clear()
        self.resultados = []
        self.tabla.setRowCount(0)
        self.card_movimientos.label_valor.setText("0")
        self.card_total.label_valor.setText("$0")
        self.boton_exportar.setEnabled(False)

    def filtrar(self):
        fecha_inicio = self.fecha_inicio.date().toPython()
        fecha_fin = self.fecha_fin.date().toPython()
        patente = self.input_patente.text().strip().upper()

        self.resultados = obtener_reportes(fecha_inicio, fecha_fin, patente)

        if not self.resultados:
            self.tabla.setRowCount(0)
            self.card_movimientos.label_valor.setText("0")
            self.card_total.label_valor.setText("$0")
            self.boton_exportar.setEnabled(False)
            QMessageBox.information(self, "Sin resultados", "No se encontraron movimientos en ese rango.")
            return

        self.tabla.setRowCount(len(self.resultados) + 1)
        total = 0

        for i, row in enumerate(self.resultados):
            ingreso = row["fecha_hora_ingreso"].strftime("%d-%m-%Y %H:%M")
            salida = row["fecha_hora_salida"].strftime("%d-%m-%Y %H:%M")
            tarifa = row["tarifa_aplicada"]
            total += tarifa

            item_patente = QTableWidgetItem(row["patente"])
            item_ingreso = QTableWidgetItem(ingreso)
            item_salida = QTableWidgetItem(salida)
            item_minutos = QTableWidgetItem(str(row["minutos"]))
            item_monto = QTableWidgetItem(f"${tarifa:.0f}")

            item_patente.setTextAlignment(Qt.AlignCenter)
            item_minutos.setTextAlignment(Qt.AlignCenter)
            item_monto.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.tabla.setItem(i, 0, item_patente)
            self.tabla.setItem(i, 1, item_ingreso)
            self.tabla.setItem(i, 2, item_salida)
            self.tabla.setItem(i, 3, item_minutos)
            self.tabla.setItem(i, 4, item_monto)

        fila_total = len(self.resultados)

        self.tabla.setItem(fila_total, 0, QTableWidgetItem(""))
        self.tabla.setItem(fila_total, 1, QTableWidgetItem(""))
        self.tabla.setItem(fila_total, 2, QTableWidgetItem(""))

        item_total_label = QTableWidgetItem("TOTAL RECAUDADO:")
        item_total_label.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

        item_total_valor = QTableWidgetItem(f"${total:.0f}")
        item_total_valor.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.tabla.setItem(fila_total, 3, item_total_label)
        self.tabla.setItem(fila_total, 4, item_total_valor)

        for col in range(self.tabla.columnCount()):
            item = self.tabla.item(fila_total, col)
            if item:
                fuente = item.font()
                fuente.setBold(True)
                item.setFont(fuente)

        self.card_movimientos.label_valor.setText(str(len(self.resultados)))
        self.card_total.label_valor.setText(f"${total:.0f}")
        self.boton_exportar.setEnabled(True)

    def exportar_pdf(self):
        if self.resultados:
            exportar_pdf(self.resultados)
        else:
            QMessageBox.information(self, "Aviso", "Primero realiza una búsqueda para poder exportar.")