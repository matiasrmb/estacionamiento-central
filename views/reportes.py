from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QDateEdit,
    QMessageBox, QFrame, QGridLayout, QSizePolicy,
    QComboBox, QTimeEdit, QCompleter, QInputDialog
)
from PySide6.QtCore import QDate, QTime, Qt

from controllers.reportes_controller import (
    obtener_reportes,
    obtener_resumen_dashboard_reportes,
    obtener_inventario_auditoria,
    obtener_reporte_cerrado,
    obtener_operaciones_reporte_cerrado,
    exportar_reporte_cerrado,
    exportar_pdf,
)
from controllers.registro_controller import obtener_patentes_conocidas
from controllers.usuarios_controller import obtener_usuarios
from utils.table_filters import create_sortable_item, sort_table_from_header_click


def _inventario_auditoria_vacio(api_error=None, source_state="unavailable"):
    return {
        "ok": False,
        "source": "api",
        "source_state": source_state,
        "period_id": None,
        "coverage": [],
        "available_sources": [],
        "partial_sources": [],
        "unavailable_sources": [],
        "affected_scopes": [],
        "unavailable_history": [],
        "requires_event_sourcing": False,
        "supports_persisted_anomalies": False,
        "unsupported_behaviors": [],
        "api_error": api_error,
    }


class ReportesWindow(QWidget):
    """
    Vista para consultar y exportar reportes de ingresos y salidas
    de vehículos por rango de fechas y patente.
    """

    def __init__(self, api_token=None):
        super().__init__()
        self.api_token = api_token
        self.setMinimumSize(900, 600)
        self.resultados = {"items": [], "totals": {}}
        self.ultimos_filtros = None
        self.reporte_cerrado_actual = None
        self.operaciones_offset = 0
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
        self.cargar_autocomplete_patentes()

        label_usuario = QLabel("Usuario")
        label_usuario.setObjectName("EtiquetaFormulario")
        self.combo_usuario = QComboBox()
        self.combo_usuario.setMinimumHeight(38)
        self.cargar_usuarios()

        label_movimiento = QLabel("Movimiento")
        label_movimiento.setObjectName("EtiquetaFormulario")
        self.combo_movimiento = QComboBox()
        self.combo_movimiento.setMinimumHeight(38)
        self.combo_movimiento.addItem("Todos", "todos")
        self.combo_movimiento.addItem("Solo ingresos", "ingresos")
        self.combo_movimiento.addItem("Solo salidas", "salidas")

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
        filtros_layout.addWidget(label_movimiento, 2, 2)
        filtros_layout.addWidget(self.combo_movimiento, 2, 3)
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
        # RESUMEN CANÓNICO 1.3.0
        # =========================================================
        dashboard_group = QFrame()
        dashboard_group.setObjectName("PanelFormulario")
        dashboard_layout = QVBoxLayout(dashboard_group)
        dashboard_layout.setContentsMargins(14, 14, 14, 14)
        dashboard_layout.setSpacing(8)

        dashboard_header = QHBoxLayout()
        self.label_centro_inteligencia = QLabel("Centro de Inteligencia · Reportes y auditoría")
        self.label_centro_inteligencia.setObjectName("TituloResumenModulo")
        dashboard_titulo = self.label_centro_inteligencia
        dashboard_titulo.setObjectName("TituloResumenModulo")
        self.label_dashboard_estado = QLabel("Fuente: reporte local")
        self.label_dashboard_estado.setObjectName("SubtituloSeccion")
        self.label_dashboard_estado.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.label_dashboard_estado.setWordWrap(True)
        dashboard_header.addWidget(dashboard_titulo)
        dashboard_header.addStretch()
        dashboard_header.addWidget(self.label_dashboard_estado)

        self.dashboard_metricas_layout = QHBoxLayout()
        self.dashboard_metricas_layout.setSpacing(12)
        self.dashboard_metric_cards = []

        self.label_dashboard_completitud = QLabel("")
        self.label_dashboard_completitud.setObjectName("SubtituloSeccion")
        self.label_dashboard_completitud.setWordWrap(True)
        self.label_dashboard_capacidad = QLabel("Capacity: unavailable")
        self.label_dashboard_capacidad.setObjectName("SubtituloSeccion")
        self.label_dashboard_capacidad.setWordWrap(True)
        self.label_dashboard_auditoria = QLabel("Audit: not provided by reporting dashboard")
        self.label_dashboard_auditoria.setObjectName("SubtituloSeccion")
        self.label_dashboard_auditoria.setWordWrap(True)
        self.label_dashboard_advertencias = QLabel("")
        self.label_dashboard_advertencias.setObjectName("SubtituloSeccion")
        self.label_dashboard_advertencias.setWordWrap(True)
        self.label_audit_inventory_estado = QLabel("Audit inventory: unavailable")
        self.label_audit_inventory_estado.setObjectName("SubtituloSeccion")
        self.label_audit_inventory_estado.setWordWrap(True)
        self.label_audit_inventory_coverage = QLabel("Coverage: No API-supplied coverage")
        self.label_audit_inventory_coverage.setObjectName("SubtituloSeccion")
        self.label_audit_inventory_coverage.setWordWrap(True)
        self.label_audit_inventory_limitaciones = QLabel("Limitations: unavailable")
        self.label_audit_inventory_limitaciones.setObjectName("SubtituloSeccion")
        self.label_audit_inventory_limitaciones.setWordWrap(True)
        self._actualizar_resumen_dashboard_local(self.resultados)

        dashboard_layout.addLayout(dashboard_header)
        dashboard_layout.addLayout(self.dashboard_metricas_layout)
        dashboard_layout.addWidget(self.label_dashboard_completitud)
        dashboard_layout.addWidget(self.label_dashboard_capacidad)
        dashboard_layout.addWidget(self.label_dashboard_auditoria)
        dashboard_layout.addWidget(self.label_dashboard_advertencias)
        dashboard_layout.addWidget(self.label_audit_inventory_estado)
        dashboard_layout.addWidget(self.label_audit_inventory_coverage)
        dashboard_layout.addWidget(self.label_audit_inventory_limitaciones)
        layout.addWidget(dashboard_group)

        # =========================================================
        # CLOSED REPORTS / API EXPORTS
        # =========================================================
        closed_group = QFrame()
        closed_group.setObjectName("PanelFormulario")
        closed_layout = QVBoxLayout(closed_group)
        closed_layout.setContentsMargins(14, 14, 14, 14)
        closed_layout.setSpacing(8)

        closed_header = QHBoxLayout()
        closed_title = QLabel("Closed report from API")
        closed_title.setObjectName("TituloResumenModulo")
        self.label_reporte_cerrado_estado = QLabel("No closed report loaded")
        self.label_reporte_cerrado_estado.setObjectName("SubtituloSeccion")
        self.label_reporte_cerrado_estado.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.label_reporte_cerrado_estado.setWordWrap(True)

        self.boton_reportes_cerrados = QPushButton("Load closed report")
        self.boton_reportes_cerrados.setObjectName("BotonSecundario")
        self.boton_reportes_cerrados.clicked.connect(self.cargar_reporte_cerrado)
        self.boton_exportacion_canonica = QPushButton("Export closed PDF")
        self.boton_exportacion_canonica.setObjectName("BotonSecundario")
        self.boton_exportacion_canonica.clicked.connect(lambda: self.exportar_reporte_cerrado_api("pdf"))
        self.boton_exportacion_canonica.setVisible(False)
        self.boton_exportacion_canonica.setEnabled(False)
        self.boton_exportacion_canonica_xlsx = QPushButton("Export closed XLSX")
        self.boton_exportacion_canonica_xlsx.setObjectName("BotonSecundario")
        self.boton_exportacion_canonica_xlsx.clicked.connect(lambda: self.exportar_reporte_cerrado_api("xlsx"))
        self.boton_exportacion_canonica_xlsx.setVisible(False)
        self.boton_exportacion_canonica_xlsx.setEnabled(False)
        self.label_exportaciones_diferidas = QLabel("PDF/XLSX exports are deferred to 1.3.x.")
        self.label_exportaciones_diferidas.setObjectName("SubtituloSeccion")
        self.label_exportaciones_diferidas.setWordWrap(True)
        self._actualizar_estado_exportaciones_cerradas()

        closed_header.addWidget(closed_title)
        closed_header.addStretch()
        closed_header.addWidget(self.label_reporte_cerrado_estado)
        closed_header.addWidget(self.boton_reportes_cerrados)
        closed_header.addWidget(self.boton_exportacion_canonica)
        closed_header.addWidget(self.boton_exportacion_canonica_xlsx)

        self.reporte_cerrado_metricas_layout = QHBoxLayout()
        self.reporte_cerrado_metricas_layout.setSpacing(12)
        self.card_reporte_cerrado_bruto = self.crear_tarjeta_resumen("Total bruto", "$0")
        self.card_reporte_cerrado_gastos = self.crear_tarjeta_resumen("Gastos", "$0")
        self.card_reporte_cerrado_neto = self.crear_tarjeta_resumen("Total neto", "$0")
        self.reporte_cerrado_metric_cards = [
            self.card_reporte_cerrado_bruto,
            self.card_reporte_cerrado_gastos,
            self.card_reporte_cerrado_neto,
        ]
        for card in self.reporte_cerrado_metric_cards:
            self.reporte_cerrado_metricas_layout.addWidget(card)
        self.reporte_cerrado_metricas_layout.addStretch()

        self.label_reporte_cerrado_periodo = QLabel("Period: unavailable")
        self.label_reporte_cerrado_periodo.setObjectName("SubtituloSeccion")
        self.label_reporte_cerrado_periodo.setWordWrap(True)
        self.label_reporte_cerrado_fuente = QLabel("Source: unavailable")
        self.label_reporte_cerrado_fuente.setObjectName("SubtituloSeccion")
        self.label_reporte_cerrado_fuente.setWordWrap(True)
        self.label_reporte_cerrado_completitud = QLabel("Completeness: unavailable")
        self.label_reporte_cerrado_completitud.setObjectName("SubtituloSeccion")
        self.label_reporte_cerrado_completitud.setWordWrap(True)
        self.label_reporte_cerrado_capacidad = QLabel("Capacity: unavailable")
        self.label_reporte_cerrado_capacidad.setObjectName("SubtituloSeccion")
        self.label_reporte_cerrado_capacidad.setWordWrap(True)
        self.label_reporte_cerrado_advertencias = QLabel("")
        self.label_reporte_cerrado_advertencias.setObjectName("SubtituloSeccion")
        self.label_reporte_cerrado_advertencias.setWordWrap(True)

        operations_controls = QGridLayout()
        operations_controls.setHorizontalSpacing(10)
        operations_controls.setVerticalSpacing(8)
        self.input_operacion_categoria = QLineEdit()
        self.input_operacion_categoria.setPlaceholderText("Category")
        self.input_operacion_operador = QLineEdit()
        self.input_operacion_operador.setPlaceholderText("Operator")
        self.input_operacion_patente = QLineEdit()
        self.input_operacion_patente.setPlaceholderText("Plate")
        self.combo_operacion_orden = QComboBox()
        self.combo_operacion_orden.addItems(["timestamp", "category", "amount", "operator", "plate"])
        self.combo_operacion_direccion = QComboBox()
        self.combo_operacion_direccion.addItems(["desc", "asc"])
        self.combo_operacion_limite = QComboBox()
        self.combo_operacion_limite.addItems(["10", "25", "50"])
        self.combo_operacion_limite.setCurrentText("25")
        self.boton_operaciones_buscar = QPushButton("Load operations")
        self.boton_operaciones_buscar.setObjectName("BotonSecundario")
        self.boton_operaciones_buscar.clicked.connect(self._buscar_operaciones_desde_inicio)
        self.boton_operaciones_anterior = QPushButton("Previous")
        self.boton_operaciones_anterior.setObjectName("BotonSecundario")
        self.boton_operaciones_anterior.clicked.connect(self._operaciones_pagina_anterior)
        self.boton_operaciones_siguiente = QPushButton("Next")
        self.boton_operaciones_siguiente.setObjectName("BotonSecundario")
        self.boton_operaciones_siguiente.clicked.connect(self._operaciones_pagina_siguiente)
        self.boton_operaciones_anterior.setEnabled(False)
        self.boton_operaciones_siguiente.setEnabled(False)

        operations_controls.addWidget(QLabel("Category"), 0, 0)
        operations_controls.addWidget(self.input_operacion_categoria, 0, 1)
        operations_controls.addWidget(QLabel("Operator"), 0, 2)
        operations_controls.addWidget(self.input_operacion_operador, 0, 3)
        operations_controls.addWidget(QLabel("Plate"), 0, 4)
        operations_controls.addWidget(self.input_operacion_patente, 0, 5)
        operations_controls.addWidget(QLabel("Sort"), 1, 0)
        operations_controls.addWidget(self.combo_operacion_orden, 1, 1)
        operations_controls.addWidget(QLabel("Direction"), 1, 2)
        operations_controls.addWidget(self.combo_operacion_direccion, 1, 3)
        operations_controls.addWidget(QLabel("Limit"), 1, 4)
        operations_controls.addWidget(self.combo_operacion_limite, 1, 5)
        operations_controls.addWidget(self.boton_operaciones_buscar, 1, 6)
        operations_controls.addWidget(self.boton_operaciones_anterior, 2, 5)
        operations_controls.addWidget(self.boton_operaciones_siguiente, 2, 6)

        self.label_operaciones_estado = QLabel("Operations: load a closed report to inspect API-owned rows.")
        self.label_operaciones_estado.setObjectName("SubtituloSeccion")
        self.label_operaciones_estado.setWordWrap(True)
        self.label_operaciones_paginacion = QLabel("Pagination: unavailable")
        self.label_operaciones_paginacion.setObjectName("SubtituloSeccion")
        self.label_operaciones_paginacion.setWordWrap(True)
        self.label_operaciones_advertencias = QLabel("")
        self.label_operaciones_advertencias.setObjectName("SubtituloSeccion")
        self.label_operaciones_advertencias.setWordWrap(True)
        self.tabla_operaciones_reporte = QTableWidget()
        self.tabla_operaciones_reporte.setColumnCount(5)
        self.tabla_operaciones_reporte.setHorizontalHeaderLabels(["Category", "Amount", "Operator", "Plate", "Timestamp"])
        self.tabla_operaciones_reporte.setAlternatingRowColors(True)
        self.tabla_operaciones_reporte.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_operaciones_reporte.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla_operaciones_reporte.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        closed_layout.addLayout(closed_header)
        closed_layout.addWidget(self.label_exportaciones_diferidas)
        closed_layout.addLayout(self.reporte_cerrado_metricas_layout)
        closed_layout.addWidget(self.label_reporte_cerrado_periodo)
        closed_layout.addWidget(self.label_reporte_cerrado_fuente)
        closed_layout.addWidget(self.label_reporte_cerrado_completitud)
        closed_layout.addWidget(self.label_reporte_cerrado_capacidad)
        closed_layout.addWidget(self.label_reporte_cerrado_advertencias)
        closed_layout.addLayout(operations_controls)
        closed_layout.addWidget(self.label_operaciones_estado)
        closed_layout.addWidget(self.label_operaciones_paginacion)
        closed_layout.addWidget(self.label_operaciones_advertencias)
        closed_layout.addWidget(self.tabla_operaciones_reporte)
        layout.addWidget(closed_group)

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

        self.label_reportes_locales_legacy = QLabel("legacy/local calendar report consultation")
        self.label_reportes_locales_legacy.setObjectName("SubtituloSeccion")
        self.label_reportes_locales_legacy.setWordWrap(True)
        layout.addWidget(self.label_reportes_locales_legacy)
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

    def cargar_autocomplete_patentes(self):
        try:
            patentes = obtener_patentes_conocidas()
        except Exception:
            patentes = []
        self.completer_patentes = QCompleter(patentes, self)
        self.completer_patentes.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer_patentes.setFilterMode(Qt.MatchContains)
        self.input_patente.setCompleter(self.completer_patentes)

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
        self.combo_movimiento.setCurrentIndex(0)
        self.resultados = {"items": [], "totals": {}}
        self.tabla.setRowCount(0)
        self.card_movimientos.label_valor.setText("0")
        self.card_total.label_valor.setText("$0")
        self.card_gastos.label_valor.setText("$0")
        self.card_neto.label_valor.setText("$0")
        self._actualizar_resumen_dashboard_local(self.resultados)
        self.boton_exportar.setEnabled(False)

    def filtrar(self):
        fecha_inicio = self.fecha_inicio.date().toPython()
        fecha_fin = self.fecha_fin.date().toPython()
        patente = self.input_patente.text().strip().upper()
        hora_inicio = self.hora_inicio.time().toPython()
        hora_fin = self.hora_fin.time().toPython()
        usuario = self.combo_usuario.currentData() or ""
        movimiento = self.combo_movimiento.currentData() or "todos"

        self.resultados = obtener_reportes(fecha_inicio, fecha_fin, patente, hora_inicio, hora_fin, usuario, movimiento)
        items = self.resultados.get("items", [])
        totals = self.resultados.get("totals", {})
        self._actualizar_resumen_dashboard(fecha_inicio, fecha_fin)
        self.ultimos_filtros = {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "patente": patente,
            "hora_inicio": hora_inicio,
            "hora_fin": hora_fin,
            "usuario": usuario,
            "movimiento": movimiento,
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
            ingreso_valor = row.get("fecha_hora_ingreso")
            salida_valor = row.get("fecha_hora_salida")
            minutos = row.get("minutos")
            tarifa = row.get("tarifa_aplicada")
            ingreso = ingreso_valor.strftime("%d-%m-%Y %H:%M") if ingreso_valor else "-"
            salida = salida_valor.strftime("%d-%m-%Y %H:%M") if salida_valor else "-"
            minutos_texto = str(minutos) if minutos is not None else "-"
            tarifa_valor = tarifa or 0
            categoria = row.get("categoria", "")
            usuario_row = row.get("usuario") or "-"

            item_categoria = create_sortable_item(categoria)
            item_patente = create_sortable_item(row["patente"])
            item_ingreso = create_sortable_item(ingreso, sort_value=ingreso_valor or "")
            item_salida = create_sortable_item(salida, sort_value=salida_valor or "")
            item_minutos = create_sortable_item(minutos_texto, sort_value=minutos or 0)
            item_usuario = create_sortable_item(usuario_row)
            item_monto = create_sortable_item(f"${tarifa_valor:.0f}", sort_value=tarifa_valor)

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

    def _actualizar_resumen_dashboard(self, fecha_inicio, fecha_fin):
        try:
            payload = obtener_resumen_dashboard_reportes(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                token=self.api_token,
            )
        except Exception:
            self._actualizar_resumen_dashboard_local(self.resultados)
            return

        if payload.get("source") == "api":
            self._actualizar_resumen_dashboard_api(payload)
        else:
            self._actualizar_resumen_dashboard_local(payload)
        self._actualizar_inventario_auditoria()

    def _actualizar_inventario_auditoria(self):
        if not self.api_token:
            self._renderizar_inventario_auditoria(_inventario_auditoria_vacio("Sin sesión API"))
            return
        try:
            payload = obtener_inventario_auditoria(self.api_token)
        except Exception as exc:
            payload = _inventario_auditoria_vacio(str(exc), source_state="api_error")
        self._renderizar_inventario_auditoria(payload)

    def _renderizar_inventario_auditoria(self, payload):
        payload = payload or {}
        period_id = payload.get("period_id") or "current"
        source_state = payload.get("source_state") or "unavailable"
        api_error = payload.get("api_error")
        if payload.get("ok"):
            self.label_audit_inventory_estado.setText(f"Audit inventory · Period: {period_id} · Source: {source_state}")
        elif source_state == "api_error":
            self.label_audit_inventory_estado.setText(f"Inventory error: {api_error or 'API request failed'} · Period: {period_id}")
        else:
            self.label_audit_inventory_estado.setText("Inventory unavailable: API did not provide validated readiness data")

        coverage = payload.get("coverage") or []
        if coverage:
            coverage_text = "; ".join(
                f"{item.get('source') or 'unknown'} ({item.get('state') or 'unavailable'})"
                for item in coverage
            )
            self.label_audit_inventory_coverage.setText(f"Coverage: {coverage_text}")
        else:
            self.label_audit_inventory_coverage.setText("Coverage: No API-supplied coverage")

        parts = [
            f"Available: {self._compactar_lista_metadata(payload.get('available_sources') or []) or 'unavailable'}",
            f"Partial: {self._compactar_lista_metadata(payload.get('partial_sources') or []) or 'unavailable'}",
            f"Unavailable: {self._compactar_lista_metadata(payload.get('unavailable_sources') or []) or 'unavailable'}",
            f"Affected scopes: {self._compactar_lista_metadata(payload.get('affected_scopes') or []) or 'unavailable'}",
            f"Unavailable history: {self._compactar_lista_metadata(payload.get('unavailable_history') or []) or 'unavailable'}",
            f"Event sourcing required: {'yes' if payload.get('requires_event_sourcing') else 'no'}",
            f"Persisted anomalies supported: {'yes' if payload.get('supports_persisted_anomalies') else 'no'}",
            f"Unsupported behaviors: {self._compactar_lista_metadata(payload.get('unsupported_behaviors') or []) or 'unavailable'}",
        ]
        if not payload.get("ok"):
            parts.append("No local fallback coverage is used")
        self.label_audit_inventory_limitaciones.setText("Limitations: " + " · ".join(parts))

    def _actualizar_resumen_dashboard_api(self, payload):
        version = payload.get("catalog_version") or "no disponible"
        periodo = payload.get("period", {}) or {}
        periodo_texto = payload.get("period_state") or periodo.get("state") or periodo.get("id") or "open"
        source_state = payload.get("source_state") or payload.get("source") or "api"
        self.label_dashboard_estado.setText(
            f"Fuente: API reporting · Periodo: {periodo_texto} · Fuente datos: {source_state} · Versión catálogo: {version}"
        )
        self._actualizar_metadata_dashboard(payload)
        metricas = []
        for metrica in payload.get("summary", []):
            nombre = metrica.get("metric") or ""
            etiqueta = self._etiqueta_metrica_dashboard(nombre, metrica.get("label"))
            metricas.append((etiqueta, self._formatear_valor_metrica(nombre, metrica.get("value", 0))))
        self._renderizar_metricas_dashboard(metricas)

    def _actualizar_resumen_dashboard_local(self, payload):
        totals = (payload or {}).get("totals", {})
        source = (payload or {}).get("source")
        source_state = (payload or {}).get("source_state") or source or "local"
        period_state = (payload or {}).get("period_state") or "open"
        if source == "local_fallback":
            estado = f"Fuente: reporte local · Periodo: {period_state} · Fuente datos: {source_state} · API no disponible"
            if (payload or {}).get("official") is False or source_state == "local_fallback":
                estado = f"{estado} · No oficial"
        elif not self.api_token:
            estado = f"Fuente: reporte local · Periodo: {period_state} · Fuente datos: {source_state} · Sin sesión API"
        else:
            estado = f"Fuente: reporte local · Periodo: {period_state} · Fuente datos: {source_state}"
        self.label_dashboard_estado.setText(estado)
        self._actualizar_metadata_dashboard(payload or {})
        self._renderizar_metricas_dashboard([
            ("Total bruto", f"${totals.get('total_general', 0):.0f}"),
            ("Gastos", f"${totals.get('total_gastos', 0):.0f}"),
            ("Total neto", f"${totals.get('total_neto', 0):.0f}"),
        ])

    def _actualizar_metadata_dashboard(self, payload):
        completeness = payload.get("completeness") or {"state": "complete", "reason": None}
        state = completeness.get("state") or "complete"
        reason = completeness.get("reason")
        if state == "incomplete":
            text = "Incomplete totals: available values are shown, but totals may be incomplete."
            if reason:
                text = f"{text} Reason: {reason}"
        else:
            text = "Completeness: complete"
        self.label_dashboard_completitud.setText(text)
        self.label_dashboard_capacidad.setText(self._texto_capacidad_dashboard(payload.get("capacity")))
        self.label_dashboard_auditoria.setText(self._texto_auditoria_dashboard(payload))
        warnings = payload.get("warnings") or []
        if not warnings and payload.get("source_state") == "local_fallback":
            warnings = ["Local fallback is not official closure truth."]
        self.label_dashboard_advertencias.setText("Warnings: " + "; ".join(warnings) if warnings else "")

    @staticmethod
    def _texto_auditoria_dashboard(payload):
        if payload.get("source_state") == "local_fallback" or payload.get("source") == "local_fallback":
            return "Audit: unavailable - local non-official fallback; API audit coverage unavailable"

        coverage = payload.get("audit_coverage") or {}
        if not coverage or not isinstance(coverage, dict):
            return "Audit: not provided by reporting dashboard"

        state = coverage.get("state") or "not_provided"
        available = ReportesWindow._compactar_lista_metadata(coverage.get("available") or [])
        gaps = ReportesWindow._compactar_lista_metadata(coverage.get("gaps") or [])
        unavailable = ReportesWindow._compactar_lista_metadata(coverage.get("unavailable") or [])
        notes = ReportesWindow._compactar_lista_metadata(coverage.get("notes") or [])

        if state == "available" and available:
            text = f"Audit: available - {available}"
            if gaps:
                text = f"{text}; Gaps: {gaps}"
            return text
        if state == "gap":
            text = f"Audit: gaps - {gaps or 'not specified'}"
            if available:
                text = f"{text}; Available: {available}"
            return text
        if state == "unavailable":
            text = f"Audit: unavailable - {unavailable or notes or 'coverage unavailable'}"
            if notes and unavailable:
                text = f"{text}; Notes: {notes}"
            return text
        return "Audit: not provided by reporting dashboard"

    @staticmethod
    def _compactar_lista_metadata(items):
        items = [str(item) for item in (items or []) if item is not None and str(item)]
        if not items:
            return ""
        if len(items) <= 3:
            return ", ".join(items)
        return f"{', '.join(items[:3])} (+{len(items) - 3} more)"

    @staticmethod
    def _texto_capacidad_dashboard(capacity):
        if not capacity:
            return "Capacity: unavailable"
        total = capacity.get("total")
        occupied = capacity.get("occupied")
        available = capacity.get("available")
        parts = []
        if total is not None:
            parts.append(f"total {total}")
        if occupied is not None:
            parts.append(f"occupied {occupied}")
        if available is not None:
            parts.append(f"available {available}")
        if not parts:
            return "Capacity: unavailable"
        state = capacity.get("state")
        if state:
            parts.append(f"state {state}")
        return f"Capacity: {', '.join(parts)}"

    def _renderizar_metricas_dashboard(self, metricas):
        while self.dashboard_metricas_layout.count():
            item = self.dashboard_metricas_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.dashboard_metric_cards = []
        for titulo, valor in metricas[:4]:
            tarjeta = self.crear_tarjeta_resumen(titulo, valor)
            self.dashboard_metricas_layout.addWidget(tarjeta)
            self.dashboard_metric_cards.append(tarjeta)
        self.dashboard_metricas_layout.addStretch()

    @staticmethod
    def _etiqueta_metrica_dashboard(nombre, etiqueta_api=None):
        etiquetas = {
            "operational_income_total": "Total ingresos operacionales",
            "operational_expense_total": "Gastos operacionales",
            "operational_net_total": "Neto operacional",
            "collected_sources_total": "Total recaudado",
            "net_revenue_total": "Ingreso neto",
            "monthly_payments_collected_total": "Mensualidades cobradas",
            "vehicle_movement_count": "Movimientos de vehículos",
        }
        return etiqueta_api or etiquetas.get(nombre) or nombre or "Métrica"

    def cargar_reporte_cerrado(self):
        closure_id, accepted = QInputDialog.getText(self, "Closed report", "Closure or report id:")
        closure_id = closure_id.strip()
        if not accepted or not closure_id:
            return
        payload = obtener_reporte_cerrado(self.api_token, closure_id)
        if not payload.get("ok"):
            self._mostrar_error_reporte_cerrado(payload)
            return
        self.reporte_cerrado_actual = payload
        self._renderizar_reporte_cerrado(payload)
        self.operaciones_offset = 0
        self.cargar_operaciones_reporte_cerrado()
        QMessageBox.information(self, "Closed report", "Closed report loaded from the API.")

    def _mostrar_error_reporte_cerrado(self, payload):
        detail = payload.get("api_error") or "Closed report request failed."
        status = payload.get("status")
        mensaje = f"{detail}"
        if status:
            mensaje = f"{mensaje} (status {status})"
        self.label_reporte_cerrado_advertencias.setText(mensaje)
        QMessageBox.warning(self, "Closed report error", mensaje)

    def _renderizar_reporte_cerrado(self, payload):
        report_id = payload.get("report_id") or "unavailable"
        period = payload.get("period") or {}
        closure = payload.get("closure_reference") or {}
        totals = payload.get("operation_totals") or {}
        completeness = payload.get("historical_completeness") or payload.get("completeness") or {}
        source_state = payload.get("source_state") or payload.get("source") or "api"
        catalog_version = payload.get("catalog_version") or "unavailable"

        self.label_reporte_cerrado_estado.setText(f"Report: {report_id}")
        self.label_reporte_cerrado_periodo.setText(
            f"Period: {period.get('from') or '-'} to {period.get('to') or '-'} · Closure: {closure.get('id') or '-'}"
        )
        self.label_reporte_cerrado_fuente.setText(
            f"Source: {source_state} · Catalog version: {catalog_version}"
        )
        self.label_reporte_cerrado_completitud.setText(self._texto_completitud_reporte_cerrado(completeness))
        self.label_reporte_cerrado_capacidad.setText(self._texto_capacidad_dashboard(payload.get("capacity")))
        warnings = payload.get("warnings") or []
        self.label_reporte_cerrado_advertencias.setText("Warnings: " + "; ".join(warnings) if warnings else "Warnings: none")
        self.card_reporte_cerrado_bruto.label_valor.setText(f"${totals.get('total_general', 0):.0f}")
        self.card_reporte_cerrado_gastos.label_valor.setText(f"${totals.get('total_gastos', 0):.0f}")
        self.card_reporte_cerrado_neto.label_valor.setText(f"${totals.get('total_neto', 0):.0f}")
        self._actualizar_estado_exportaciones_cerradas()

    def _closure_id_reporte_cerrado_exportable(self):
        payload = self.reporte_cerrado_actual or {}
        if payload.get("source") != "api":
            return None
        closure = payload.get("closure_reference") or {}
        return closure.get("id")

    def _actualizar_estado_exportaciones_cerradas(self, mensaje=None):
        exportable = bool(self._closure_id_reporte_cerrado_exportable())
        self.boton_exportacion_canonica.setVisible(exportable)
        self.boton_exportacion_canonica_xlsx.setVisible(exportable)
        self.boton_exportacion_canonica.setEnabled(exportable)
        self.boton_exportacion_canonica_xlsx.setEnabled(exportable)
        if mensaje:
            self.label_exportaciones_diferidas.setText(mensaje)
        elif exportable:
            self.label_exportaciones_diferidas.setText("Closed report PDF/XLSX exports are available for this API-backed closure.")
        else:
            self.label_exportaciones_diferidas.setText("Load an API-backed closed report with a closure reference to export PDF/XLSX.")

    def _operaciones_filtros(self):
        return {
            "category": self.input_operacion_categoria.text().strip(),
            "operator": self.input_operacion_operador.text().strip(),
            "plate": self.input_operacion_patente.text().strip().upper(),
            "sort": self.combo_operacion_orden.currentText(),
            "direction": self.combo_operacion_direccion.currentText(),
            "limit": int(self.combo_operacion_limite.currentText()),
            "offset": self.operaciones_offset,
        }

    def _buscar_operaciones_desde_inicio(self):
        self.operaciones_offset = 0
        self.cargar_operaciones_reporte_cerrado()

    def _operaciones_pagina_anterior(self):
        limit = int(self.combo_operacion_limite.currentText())
        self.operaciones_offset = max(0, self.operaciones_offset - limit)
        self.cargar_operaciones_reporte_cerrado()

    def _operaciones_pagina_siguiente(self):
        limit = int(self.combo_operacion_limite.currentText())
        self.operaciones_offset += limit
        self.cargar_operaciones_reporte_cerrado()

    def cargar_operaciones_reporte_cerrado(self):
        closure = (self.reporte_cerrado_actual or {}).get("closure_reference") or {}
        closure_id = closure.get("id")
        if not closure_id:
            self.label_operaciones_estado.setText("Operations: load a closed report before requesting rows.")
            return
        payload = obtener_operaciones_reporte_cerrado(
            self.api_token,
            closure_id,
            **self._operaciones_filtros(),
        )
        self._renderizar_operaciones_reporte(payload)

    def _renderizar_operaciones_reporte(self, payload):
        if not payload.get("ok"):
            detail = payload.get("api_error") or "Operation request failed."
            status = payload.get("status")
            suffix = f" (status {status})" if status else ""
            self.label_operaciones_estado.setText(f"Operations error: {detail}{suffix}")
            self.label_operaciones_paginacion.setText("Pagination: unavailable")
            self.label_operaciones_advertencias.setText("")
            self.tabla_operaciones_reporte.setRowCount(0)
            self.boton_operaciones_anterior.setEnabled(False)
            self.boton_operaciones_siguiente.setEnabled(False)
            return

        rows = payload.get("rows") or []
        self.tabla_operaciones_reporte.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            amount = row.get("amount") or 0
            items = [
                QTableWidgetItem(str(row.get("category") or "-")),
                QTableWidgetItem(f"${float(amount):.0f}"),
                QTableWidgetItem(str(row.get("operator") or "-")),
                QTableWidgetItem(str(row.get("plate") or "-")),
                QTableWidgetItem(str(row.get("timestamp") or "-")),
            ]
            items[1].setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            for column, item in enumerate(items):
                self.tabla_operaciones_reporte.setItem(row_index, column, item)

        pagination = payload.get("pagination") or {}
        limit = int(pagination.get("limit") or self.combo_operacion_limite.currentText())
        offset = int(pagination.get("offset") or 0)
        total = int(pagination.get("total") or len(rows))
        start = offset + 1 if total else 0
        end = min(offset + limit, total) if total else 0
        self.label_operaciones_paginacion.setText(f"Pagination: {start}-{end} of {total}")
        if total == 1 and len(rows) == 1:
            self.label_operaciones_paginacion.setText("Pagination: 1 of 1")
        self.label_operaciones_estado.setText("Operations loaded from API." if rows else "No operations found for this closed report.")
        warnings = payload.get("warnings") or []
        self.label_operaciones_advertencias.setText("Warnings: " + "; ".join(warnings) if warnings else "")
        self.boton_operaciones_anterior.setEnabled(offset > 0)
        self.boton_operaciones_siguiente.setEnabled(offset + limit < total)

    @staticmethod
    def _texto_completitud_reporte_cerrado(completeness):
        state = completeness.get("state") or "complete"
        reason = completeness.get("reason")
        if state == "incomplete":
            text = "Incomplete totals: available values are shown, but totals may be incomplete."
            if reason:
                text = f"{text} Reason: {reason}"
            return text
        return f"Completeness: {state}"

    def exportar_reporte_cerrado_api(self, formato):
        closure_id = self._closure_id_reporte_cerrado_exportable()
        if not closure_id:
            QMessageBox.warning(self, "Closed report export", "Load a closed report before exporting.")
            return
        result = exportar_reporte_cerrado(self.api_token, closure_id, formato)
        if not result.get("ok"):
            detail = result.get("api_error") or "Closed report export failed."
            status = result.get("status")
            mensaje = f"{detail} (status {status})" if status else detail
            self._actualizar_estado_exportaciones_cerradas(f"Export error: {mensaje}")
            QMessageBox.warning(self, "Closed report export error", mensaje)
            return
        path = result.get("path") or "file saved"
        self._actualizar_estado_exportaciones_cerradas(f"Export saved: {path}")
        QMessageBox.information(self, "Closed report export", f"Export saved: {path}")

    @staticmethod
    def _formatear_valor_metrica(nombre, valor):
        try:
            numero = float(valor or 0)
        except (TypeError, ValueError):
            return str(valor)
        if nombre.endswith("_count") or nombre.endswith("_quantity"):
            return f"{numero:.0f}"
        return f"${numero:.0f}"

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
