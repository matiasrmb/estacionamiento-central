from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QDateEdit,
    QMessageBox, QFrame, QGridLayout, QSizePolicy,
    QComboBox, QTimeEdit, QCompleter
)
from PySide6.QtCore import QDate, QTime, Qt

from controllers.reportes_controller import (
    obtener_reportes,
    obtener_resumen_dashboard_reportes,
    exportar_pdf,
)
from controllers.registro_controller import obtener_patentes_conocidas
from controllers.usuarios_controller import obtener_usuarios
from utils.table_filters import create_sortable_item, sort_table_from_header_click


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
        dashboard_titulo = QLabel("Resumen canónico 1.3.0")
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
        self._actualizar_resumen_dashboard_local(self.resultados)

        dashboard_layout.addLayout(dashboard_header)
        dashboard_layout.addLayout(self.dashboard_metricas_layout)
        layout.addWidget(dashboard_group)

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

    def _actualizar_resumen_dashboard_api(self, payload):
        version = payload.get("catalog_version") or "no disponible"
        periodo = payload.get("period", {}) or {}
        periodo_texto = periodo.get("id") or "actual"
        self.label_dashboard_estado.setText(
            f"Fuente: API reporting · Período: {periodo_texto} · Versión catálogo: {version}"
        )
        metricas = []
        for metrica in payload.get("summary", []):
            nombre = metrica.get("metric") or ""
            etiqueta = self._etiqueta_metrica_dashboard(nombre, metrica.get("label"))
            metricas.append((etiqueta, self._formatear_valor_metrica(nombre, metrica.get("value", 0))))
        self._renderizar_metricas_dashboard(metricas)

    def _actualizar_resumen_dashboard_local(self, payload):
        totals = (payload or {}).get("totals", {})
        source = (payload or {}).get("source")
        if source == "local_fallback":
            estado = "Fuente: reporte local · API no disponible"
        elif not self.api_token:
            estado = "Fuente: reporte local · Sin sesión API"
        else:
            estado = "Fuente: reporte local"
        self.label_dashboard_estado.setText(estado)
        self._renderizar_metricas_dashboard([
            ("Total bruto", f"${totals.get('total_general', 0):.0f}"),
            ("Gastos", f"${totals.get('total_gastos', 0):.0f}"),
            ("Total neto", f"${totals.get('total_neto', 0):.0f}"),
        ])

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
        }
        return etiquetas.get(nombre) or etiqueta_api or nombre or "Métrica"

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
