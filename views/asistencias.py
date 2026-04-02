from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QDateEdit, QMessageBox,
    QFrame, QGridLayout, QHeaderView, QSizePolicy
)
from PySide6.QtCore import QDate, Qt

from controllers.asistencias_controller import obtener_asistencias
from utils.pdf_asistencias import exportar_asistencias_pdf


class AsistenciasWindow(QWidget):
    """
    Vista para visualizar y exportar asistencias de usuarios,
    filtradas por fecha y nombre de usuario.
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

        subtitulo = QLabel("Consulta asistencias por usuario y rango de fechas, y exporta los resultados.")
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

        label_usuario = QLabel("Usuario")
        label_usuario.setObjectName("EtiquetaFormulario")
        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Opcional")
        self.input_usuario.setMinimumHeight(38)

        label_desde = QLabel("Desde")
        label_desde.setObjectName("EtiquetaFormulario")
        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setCalendarPopup(True)
        self.fecha_inicio.setDate(QDate.currentDate())
        self.fecha_inicio.setMinimumHeight(38)

        label_hasta = QLabel("Hasta")
        label_hasta.setObjectName("EtiquetaFormulario")
        self.fecha_fin = QDateEdit()
        self.fecha_fin.setCalendarPopup(True)
        self.fecha_fin.setDate(QDate.currentDate())
        self.fecha_fin.setMinimumHeight(38)

        self.btn_filtrar = QPushButton("Buscar")
        self.btn_filtrar.setMinimumHeight(40)
        self.btn_filtrar.clicked.connect(self.filtrar)

        self.btn_limpiar = QPushButton("Limpiar filtros")
        self.btn_limpiar.setObjectName("BotonSecundario")
        self.btn_limpiar.setMinimumHeight(38)
        self.btn_limpiar.clicked.connect(self.limpiar_filtros)

        self.btn_exportar = QPushButton("Exportar PDF")
        self.btn_exportar.setMinimumHeight(40)
        self.btn_exportar.setEnabled(False)
        self.btn_exportar.clicked.connect(self.exportar_pdf)

        filtros_layout.addWidget(label_usuario, 0, 0)
        filtros_layout.addWidget(self.input_usuario, 0, 1)
        filtros_layout.addWidget(label_desde, 0, 2)
        filtros_layout.addWidget(self.fecha_inicio, 0, 3)
        filtros_layout.addWidget(label_hasta, 0, 4)
        filtros_layout.addWidget(self.fecha_fin, 0, 5)
        filtros_layout.addWidget(self.btn_filtrar, 0, 6)

        filtros_layout.addWidget(self.btn_limpiar, 1, 5)
        filtros_layout.addWidget(self.btn_exportar, 1, 6)

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

        self.card_registros = self.crear_tarjeta_resumen("Asistencias encontradas", "0")
        self.card_total = self.crear_tarjeta_resumen("Total recaudado", "$0")

        resumen_layout.addWidget(self.card_registros)
        resumen_layout.addWidget(self.card_total)
        resumen_layout.addStretch()

        layout.addLayout(resumen_layout)

        # =========================================================
        # TABLA
        # =========================================================
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels([
            "Usuario", "Hora de Inicio", "Hora de Salida", "Movimientos", "Total Recaudado"
        ])
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
        self.input_usuario.clear()
        self.fecha_inicio.setDate(QDate.currentDate())
        self.fecha_fin.setDate(QDate.currentDate())
        self.resultados = []
        self.tabla.setRowCount(0)
        self.card_registros.label_valor.setText("0")
        self.card_total.label_valor.setText("$0")
        self.btn_exportar.setEnabled(False)

    def filtrar(self):
        try:
            usuario = self.input_usuario.text().strip()
            fecha_inicio = self.fecha_inicio.date().toPython()
            fecha_fin = self.fecha_fin.date().toPython()

            datos = obtener_asistencias(usuario or None, fecha_inicio, fecha_fin)
            self.resultados = datos

            if not datos:
                self.tabla.setRowCount(0)
                self.card_registros.label_valor.setText("0")
                self.card_total.label_valor.setText("$0")
                self.btn_exportar.setEnabled(False)
                QMessageBox.information(self, "Sin resultados", "No se encontraron asistencias con esos filtros.")
                return

            self.tabla.setRowCount(len(datos))
            total_recaudado = 0

            for i, fila in enumerate(datos):
                total_fila = float(fila["total_recaudado"])
                total_recaudado += total_fila

                item_usuario = QTableWidgetItem(fila["usuario"])
                item_inicio = QTableWidgetItem(str(fila["hora_inicio"]))
                item_salida = QTableWidgetItem(str(fila["hora_salida"] or "Activo"))
                item_movs = QTableWidgetItem(str(fila["cantidad_movimientos"]))
                item_total = QTableWidgetItem(f"${total_fila:.0f}")

                item_usuario.setTextAlignment(Qt.AlignCenter)
                item_movs.setTextAlignment(Qt.AlignCenter)
                item_total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                self.tabla.setItem(i, 0, item_usuario)
                self.tabla.setItem(i, 1, item_inicio)
                self.tabla.setItem(i, 2, item_salida)
                self.tabla.setItem(i, 3, item_movs)
                self.tabla.setItem(i, 4, item_total)

            self.card_registros.label_valor.setText(str(len(datos)))
            self.card_total.label_valor.setText(f"${total_recaudado:.0f}")
            self.btn_exportar.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error:\n{e}")

    def exportar_pdf(self):
        try:
            if self.resultados:
                exportar_asistencias_pdf(self.resultados)
            else:
                QMessageBox.warning(self, "Sin datos", "Primero realiza una búsqueda con resultados.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar el PDF:\n{e}")