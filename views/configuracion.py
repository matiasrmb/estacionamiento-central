import subprocess
from pathlib import Path
from fpdf import FPDF

from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QComboBox, QMessageBox,
    QGridLayout, QSizePolicy, QFrame, QCheckBox,
    QHBoxLayout, QHeaderView, QInputDialog, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt

from controllers.config_controller import (
    LAVADO_CATEGORIAS,
    obtener_configuracion,
    actualizar_configuracion,
)
from controllers.tarifas_controller import generar_tramos_automaticos
from controllers.print_jobs_controller import (
    listar_trabajos_impresion_fallidos,
    listar_trabajos_impresion_impresos,
    crear_reimpresion_trabajo_impresion,
    reintentar_trabajo_impresion_fallido,
    reintentar_trabajo_impresion_revision_manual,
)
from utils.printer_manager import (obtener_impresoras_instaladas, 
                                   obtener_impresora_predeterminada,
                                   cargar_impresora_guardada,
                                   guardar_impresora_tickets,
)
from utils.printer_diagnostics import SUPPORTED_PRINT_PATH

class ConfiguracionWindow(QWidget):
    """
    Vista de configuración general del sistema.
    Permite definir modo de cobro, tarifas base y generar tramos automáticos.
    """

    def __init__(self, on_tramos_actualizados=None, usuario=None):
        super().__init__()
        self.on_tramos_actualizados = on_tramos_actualizados
        self.usuario = usuario
        self.setMinimumSize(900, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        subtitulo = QLabel("Define el modo de cobro y las tarifas base del estacionamiento.")
        subtitulo.setObjectName("SubtituloSeccion")
        subtitulo.setWordWrap(True)
        layout.addWidget(subtitulo)

        self.config = obtener_configuracion()

        # =========================================================
        # IMPRESIÓN OPERATIVA EN ESTA PC
        # =========================================================
        panel_print_jobs_pc = QFrame()
        panel_print_jobs_pc.setObjectName("PanelImpresionPC")
        layout_print_jobs_pc = QVBoxLayout(panel_print_jobs_pc)
        layout_print_jobs_pc.setContentsMargins(14, 14, 14, 14)
        layout_print_jobs_pc.setSpacing(6)

        titulo_print_jobs_pc = QLabel("Impresión operativa en esta PC")
        titulo_print_jobs_pc.setObjectName("EtiquetaFormulario")
        layout_print_jobs_pc.addWidget(titulo_print_jobs_pc)

        self.print_jobs_pc_activos_check = QCheckBox(
            "Crear trabajos de impresión para PC"
        )
        self.print_jobs_pc_activos_check.setObjectName("OpcionImpresionPC")
        self.print_jobs_pc_activos_check.setChecked(
            self.config.get("pc_print_jobs_activos", "1") == "1"
        )
        layout_print_jobs_pc.addWidget(self.print_jobs_pc_activos_check)

        self.print_jobs_pc_activos_label = QLabel(
            "Al desactivarlo, las nuevas operaciones no crearán trabajos para el agente de impresión."
        )
        self.print_jobs_pc_activos_label.setObjectName("SubtituloSeccion")
        self.print_jobs_pc_activos_label.setWordWrap(True)
        layout_print_jobs_pc.addWidget(self.print_jobs_pc_activos_label)
        layout.addWidget(panel_print_jobs_pc)

        # =========================================================
        # CONFIGURACIÓN GENERAL
        # =========================================================
        panel_general = QFrame()
        panel_general.setObjectName("PanelFormulario")
        layout_general_wrapper = QVBoxLayout(panel_general)
        layout_general_wrapper.setContentsMargins(14, 14, 14, 14)
        layout_general_wrapper.setSpacing(10)

        titulo_general = QLabel("Configuración general")
        titulo_general.setObjectName("EtiquetaFormulario")
        layout_general_wrapper.addWidget(titulo_general)

        layout_general = QGridLayout()
        layout_general.setHorizontalSpacing(14)
        layout_general.setVerticalSpacing(12)

        label_modo = QLabel("Modo de cobro")
        label_modo.setObjectName("EtiquetaFormulario")
        self.modo_combo = QComboBox()
        self.modo_combo.addItems(["minuto", "personalizado", "auto"])
        self.modo_combo.setCurrentText(self.config.get("modo_cobro", "minuto"))
        self.modo_combo.setMinimumHeight(38)

        label_minima = QLabel("Tarifa mínima (CLP)")
        label_minima.setObjectName("EtiquetaFormulario")
        self.minima_input = QLineEdit(self.config.get("tarifa_minima", "300"))
        self.minima_input.setMinimumHeight(38)
        self.minima_input.returnPressed.connect(self.guardar)

        label_minuto = QLabel("Tarifa por minuto (CLP)")
        label_minuto.setObjectName("EtiquetaFormulario")
        self.minuto_input = QLineEdit(self.config.get("valor_minuto", "25"))
        self.minuto_input.setMinimumHeight(38)
        self.minuto_input.returnPressed.connect(self.guardar)

        label_hora = QLabel("Tarifa por hora (CLP)")
        label_hora.setObjectName("EtiquetaFormulario")
        self.hora_input = QLineEdit(self.config.get("tarifa_hora", "1300"))
        self.hora_input.setMinimumHeight(38)
        self.hora_input.returnPressed.connect(self.guardar)

        label_bano = QLabel("Valor uso de baño (CLP)")
        label_bano.setObjectName("EtiquetaFormulario")
        self.bano_input = QLineEdit(self.config.get("valor_bano", "300"))
        self.bano_input.setMinimumHeight(38)
        self.bano_input.returnPressed.connect(self.guardar)

        layout_general.addWidget(label_modo, 0, 0)
        layout_general.addWidget(self.modo_combo, 0, 1)
        layout_general.addWidget(label_minima, 1, 0)
        layout_general.addWidget(self.minima_input, 1, 1)
        layout_general.addWidget(label_minuto, 2, 0)
        layout_general.addWidget(self.minuto_input, 2, 1)
        layout_general.addWidget(label_hora, 3, 0)
        layout_general.addWidget(self.hora_input, 3, 1)
        layout_general.addWidget(label_bano, 4, 0)
        layout_general.addWidget(self.bano_input, 4, 1)

        layout_general.setColumnStretch(1, 1)

        layout_general_wrapper.addLayout(layout_general)
        layout.addWidget(panel_general)

        # =========================================================
        # NOCHES
        # =========================================================
        panel_noches = QFrame()
        panel_noches.setObjectName("PanelFormulario")
        layout_noches_wrapper = QVBoxLayout(panel_noches)
        layout_noches_wrapper.setContentsMargins(14, 14, 14, 14)
        layout_noches_wrapper.setSpacing(10)

        titulo_noches = QLabel("Noches")
        titulo_noches.setObjectName("EtiquetaFormulario")
        layout_noches_wrapper.addWidget(titulo_noches)

        descripcion_noches = QLabel(
            "Configura el valor prepagado del modo Noche (19:30 a 09:30; gracia 19:00 a 10:00)."
        )
        descripcion_noches.setObjectName("SubtituloSeccion")
        descripcion_noches.setWordWrap(True)
        layout_noches_wrapper.addWidget(descripcion_noches)

        layout_noches = QGridLayout()
        layout_noches.setHorizontalSpacing(14)
        layout_noches.setVerticalSpacing(12)

        self.noches_activo_check = QCheckBox("Habilitar noches")
        self.noches_activo_check.setChecked(self.config.get("noches_activo", "0") == "1")
        self.noches_valor_input = QLineEdit(self.config.get("noches_valor", "0"))
        self.noches_valor_input.setMinimumHeight(38)
        self.noches_valor_input.returnPressed.connect(self.guardar)

        layout_noches.addWidget(self.noches_activo_check, 0, 0, 1, 2)
        layout_noches.addWidget(QLabel("Valor modo Noche (CLP)"), 1, 0)
        layout_noches.addWidget(self.noches_valor_input, 1, 1)
        layout_noches.setColumnStretch(1, 1)
        layout_noches_wrapper.addLayout(layout_noches)
        layout.addWidget(panel_noches)

        # =========================================================
        # LAVADOS
        # =========================================================
        panel_lavados = QFrame()
        panel_lavados.setObjectName("PanelFormulario")
        layout_lavados_wrapper = QVBoxLayout(panel_lavados)
        layout_lavados_wrapper.setContentsMargins(14, 14, 14, 14)
        layout_lavados_wrapper.setSpacing(10)

        titulo_lavados = QLabel("Valores de lavado")
        titulo_lavados.setObjectName("EtiquetaFormulario")
        layout_lavados_wrapper.addWidget(titulo_lavados)

        descripcion_lavados = QLabel(
            "Configura el valor fijo que se cobrará por lavado según el tamaño del vehículo."
        )
        descripcion_lavados.setObjectName("SubtituloSeccion")
        descripcion_lavados.setWordWrap(True)
        layout_lavados_wrapper.addWidget(descripcion_lavados)

        layout_lavados = QGridLayout()
        layout_lavados.setHorizontalSpacing(14)
        layout_lavados.setVerticalSpacing(12)

        self.lavado_inputs = {}
        for fila, (clave, etiqueta, valor_default) in enumerate(LAVADO_CATEGORIAS):
            label = QLabel(f"Lavado {etiqueta} (CLP)")
            label.setObjectName("EtiquetaFormulario")

            input_valor = QLineEdit(self.config.get(clave, valor_default))
            input_valor.setMinimumHeight(38)
            input_valor.returnPressed.connect(self.guardar)

            self.lavado_inputs[clave] = input_valor
            layout_lavados.addWidget(label, fila, 0)
            layout_lavados.addWidget(input_valor, fila, 1)

        layout_lavados.setColumnStretch(1, 1)
        layout_lavados_wrapper.addLayout(layout_lavados)
        layout.addWidget(panel_lavados)

        # =========================================================
        # LIMPIEZA AUTOMÁTICA
        # =========================================================
        panel_limpieza = QFrame()
        panel_limpieza.setObjectName("PanelFormulario")
        layout_limpieza_wrapper = QVBoxLayout(panel_limpieza)
        layout_limpieza_wrapper.setContentsMargins(14, 14, 14, 14)
        layout_limpieza_wrapper.setSpacing(10)

        titulo_limpieza = QLabel("Limpieza automática")
        titulo_limpieza.setObjectName("EtiquetaFormulario")
        layout_limpieza_wrapper.addWidget(titulo_limpieza)

        descripcion_limpieza = QLabel(
            "Elimina archivos generados antiguos de tickets, reportes, cierres, PDFs y asistencias. "
            "Nunca elimina configuración, esquema, assets ni código."
        )
        descripcion_limpieza.setObjectName("SubtituloSeccion")
        descripcion_limpieza.setWordWrap(True)
        layout_limpieza_wrapper.addWidget(descripcion_limpieza)

        layout_limpieza = QGridLayout()
        layout_limpieza.setHorizontalSpacing(14)
        layout_limpieza.setVerticalSpacing(12)

        self.limpieza_activa_check = QCheckBox("Activar limpieza automática diaria")
        self.limpieza_activa_check.setChecked(self.config.get("limpieza_automatica_activa", "1") == "1")

        label_dias_limpieza = QLabel("Días a conservar")
        label_dias_limpieza.setObjectName("EtiquetaFormulario")
        self.dias_limpieza_input = QLineEdit(self.config.get("dias_conservar_archivos", "30"))
        self.dias_limpieza_input.setMinimumHeight(38)
        self.dias_limpieza_input.returnPressed.connect(self.guardar)

        layout_limpieza.addWidget(self.limpieza_activa_check, 0, 0, 1, 2)
        layout_limpieza.addWidget(label_dias_limpieza, 1, 0)
        layout_limpieza.addWidget(self.dias_limpieza_input, 1, 1)
        layout_limpieza.setColumnStretch(1, 1)

        layout_limpieza_wrapper.addLayout(layout_limpieza)
        layout.addWidget(panel_limpieza)

        # =========================================================
        # IMPRESIÓN DE TICKETS
        # =========================================================
        panel_impresion = QFrame()
        panel_impresion.setObjectName("PanelFormulario")
        layout_impresion_wrapper = QVBoxLayout(panel_impresion)
        layout_impresion_wrapper.setContentsMargins(14, 14, 14, 14)
        layout_impresion_wrapper.setSpacing(10)

        titulo_impresion = QLabel("Impresión de tickets")
        titulo_impresion.setObjectName("EtiquetaFormulario")
        layout_impresion_wrapper.addWidget(titulo_impresion)

        descripcion_impresion = QLabel(
            "Selecciona la impresora que se utilizará para los tickets térmicos. "
            "Si la impresora configurada deja de existir, el sistema intentará usar "
            "la impresora predeterminada de Windows. "
            f"{SUPPORTED_PRINT_PATH}"
        )
        descripcion_impresion.setWordWrap(True)
        descripcion_impresion.setObjectName("SubtituloSeccion")
        layout_impresion_wrapper.addWidget(descripcion_impresion)

        layout_impresion = QGridLayout()
        layout_impresion.setHorizontalSpacing(14)
        layout_impresion.setVerticalSpacing(12)

        label_impresora = QLabel("Impresora de tickets")
        label_impresora.setObjectName("EtiquetaFormulario")

        self.impresora_combo = QComboBox()
        self.impresora_combo.setMinimumHeight(38)

        self.btn_actualizar_impresoras = QPushButton("Actualizar lista")
        self.btn_actualizar_impresoras.setMinimumHeight(38)
        self.btn_actualizar_impresoras.clicked.connect(self.cargar_impresoras_en_combo)

        self.btn_guardar_impresora = QPushButton("Guardar impresora")
        self.btn_guardar_impresora.setMinimumHeight(38)
        self.btn_guardar_impresora.clicked.connect(self.guardar_impresora_seleccionada)

        self.btn_probar_impresion = QPushButton("Probar impresión local")
        self.btn_probar_impresion.setMinimumHeight(38)
        self.btn_probar_impresion.clicked.connect(self.probar_impresion_ticket)

        self.prueba_local_label = QLabel(
            "La prueba es local y no crea un trabajo de impresión operativo."
        )
        self.prueba_local_label.setObjectName("SubtituloSeccion")
        self.prueba_local_label.setWordWrap(True)

        layout_impresion.addWidget(label_impresora, 0, 0)
        layout_impresion.addWidget(self.impresora_combo, 0, 1)
        layout_impresion.addWidget(self.btn_actualizar_impresoras, 0, 2)
        layout_impresion.addWidget(self.btn_guardar_impresora, 1, 1)
        layout_impresion.addWidget(self.btn_probar_impresion, 1, 2)
        layout_impresion.addWidget(self.prueba_local_label, 2, 0, 1, 3)

        layout_impresion.setColumnStretch(1, 1)

        layout_impresion_wrapper.addLayout(layout_impresion)

        titulo_fallidos = QLabel("Trabajos de impresión fallidos")
        titulo_fallidos.setObjectName("EtiquetaFormulario")
        layout_impresion_wrapper.addWidget(titulo_fallidos)

        self.tabla_trabajos_fallidos = QTableWidget()
        self.tabla_trabajos_fallidos.setColumnCount(8)
        self.tabla_trabajos_fallidos.setHorizontalHeaderLabels(
            ["ID", "Tipo", "Destino", "Patente", "Estado", "Intentos", "Fecha", "Error"]
        )
        self.tabla_trabajos_fallidos.setAlternatingRowColors(True)
        self.tabla_trabajos_fallidos.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_trabajos_fallidos.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla_trabajos_fallidos.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_trabajos_fallidos.setMinimumHeight(150)
        self.tabla_trabajos_fallidos.verticalHeader().setDefaultSectionSize(34)
        self.tabla_trabajos_fallidos.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #93c5fd;
                color: #111827;
            }
            QTableWidget::item:hover:!selected {
                background-color: #eff6ff;
            }
        """)

        encabezado_fallidos = self.tabla_trabajos_fallidos.horizontalHeader()
        for columna, ancho in enumerate((55, 80, 115, 90, 125, 75, 135)):
            encabezado_fallidos.setSectionResizeMode(columna, QHeaderView.Fixed)
            self.tabla_trabajos_fallidos.setColumnWidth(columna, ancho)
        encabezado_fallidos.setSectionResizeMode(7, QHeaderView.Stretch)
        layout_impresion_wrapper.addWidget(self.tabla_trabajos_fallidos)

        acciones_fallidos = QHBoxLayout()
        self.btn_actualizar_trabajos_fallidos = QPushButton("Actualizar trabajos fallidos")
        self.btn_actualizar_trabajos_fallidos.clicked.connect(self.actualizar_trabajos_impresion_fallidos)
        self.btn_reintentar_trabajo_fallido = QPushButton("Reintentar trabajo seleccionado")
        self.btn_reintentar_trabajo_fallido.clicked.connect(self.reintentar_trabajo_impresion_seleccionado)
        acciones_fallidos.addWidget(self.btn_actualizar_trabajos_fallidos)
        acciones_fallidos.addWidget(self.btn_reintentar_trabajo_fallido)
        acciones_fallidos.addStretch()
        layout_impresion_wrapper.addLayout(acciones_fallidos)

        titulo_impresos = QLabel("Trabajos de impresión ya impresos")
        titulo_impresos.setObjectName("EtiquetaFormulario")
        layout_impresion_wrapper.addWidget(titulo_impresos)

        self.tabla_trabajos_impresos = QTableWidget()
        self.tabla_trabajos_impresos.setColumnCount(6)
        self.tabla_trabajos_impresos.setHorizontalHeaderLabels(
            ["ID", "Tipo", "Destino", "Patente", "Estado", "Fecha"]
        )
        self.tabla_trabajos_impresos.setAlternatingRowColors(True)
        self.tabla_trabajos_impresos.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_trabajos_impresos.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla_trabajos_impresos.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_trabajos_impresos.setMinimumHeight(150)
        self.tabla_trabajos_impresos.verticalHeader().setDefaultSectionSize(34)
        encabezado_impresos = self.tabla_trabajos_impresos.horizontalHeader()
        for columna, ancho in enumerate((55, 110, 115, 100, 95)):
            encabezado_impresos.setSectionResizeMode(columna, QHeaderView.Fixed)
            self.tabla_trabajos_impresos.setColumnWidth(columna, ancho)
        encabezado_impresos.setSectionResizeMode(5, QHeaderView.Stretch)
        layout_impresion_wrapper.addWidget(self.tabla_trabajos_impresos)

        acciones_impresos = QHBoxLayout()
        self.btn_actualizar_trabajos_impresos = QPushButton("Actualizar trabajos impresos")
        self.btn_actualizar_trabajos_impresos.clicked.connect(self.actualizar_trabajos_impresion_impresos)
        self.btn_reimprimir_trabajo = QPushButton("Reimprimir trabajo seleccionado")
        self.btn_reimprimir_trabajo.clicked.connect(self.reimprimir_trabajo_impresion_seleccionado)
        acciones_impresos.addWidget(self.btn_actualizar_trabajos_impresos)
        acciones_impresos.addWidget(self.btn_reimprimir_trabajo)
        acciones_impresos.addStretch()
        layout_impresion_wrapper.addLayout(acciones_impresos)
        layout.addWidget(panel_impresion)

        # =========================================================
        # ACCIONES
        # =========================================================
        panel_acciones = QFrame()
        panel_acciones.setObjectName("PanelFormulario")
        layout_acciones_wrapper = QVBoxLayout(panel_acciones)
        layout_acciones_wrapper.setContentsMargins(14, 14, 14, 14)
        layout_acciones_wrapper.setSpacing(10)

        titulo_acciones = QLabel("Acciones disponibles")
        titulo_acciones.setObjectName("EtiquetaFormulario")
        layout_acciones_wrapper.addWidget(titulo_acciones)

        self.btn_generar_tramos = QPushButton("Generar tramos automáticamente")
        self.btn_generar_tramos.setMinimumHeight(40)
        self.btn_generar_tramos.clicked.connect(self.generar_tramos_auto)

        self.btn_guardar = QPushButton("Guardar configuración")
        self.btn_guardar.setMinimumHeight(40)
        self.btn_guardar.clicked.connect(self.guardar)

        self.btn_actualizar_config = QPushButton("Actualizar configuración")
        self.btn_actualizar_config.setObjectName("BotonSecundario")
        self.btn_actualizar_config.setMinimumHeight(40)
        self.btn_actualizar_config.clicked.connect(self.recargar_configuracion)

        layout_acciones_wrapper.addWidget(self.btn_generar_tramos)
        layout_acciones_wrapper.addWidget(self.btn_actualizar_config)
        layout_acciones_wrapper.addWidget(self.btn_guardar)

        layout.addWidget(panel_acciones)
        layout.addStretch()

        self.cargar_impresoras_en_combo()
        self.actualizar_trabajos_impresion_fallidos()
        self.actualizar_trabajos_impresion_impresos()
        self.setLayout(layout)

    def recargar_configuracion(self):
        self.config = obtener_configuracion()
        self.modo_combo.setCurrentText(self.config.get("modo_cobro", "minuto"))
        self.minima_input.setText(self.config.get("tarifa_minima", "300"))
        self.minuto_input.setText(self.config.get("valor_minuto", "25"))
        self.hora_input.setText(self.config.get("tarifa_hora", "1300"))
        self.bano_input.setText(self.config.get("valor_bano", "300"))
        self.noches_activo_check.setChecked(self.config.get("noches_activo", "0") == "1")
        self.noches_valor_input.setText(self.config.get("noches_valor", "0"))
        for clave, input_valor in self.lavado_inputs.items():
            valor_default = next(
                (default for item_clave, _label, default in LAVADO_CATEGORIAS if item_clave == clave),
                "0",
            )
            input_valor.setText(self.config.get(clave, valor_default))
        self.limpieza_activa_check.setChecked(self.config.get("limpieza_automatica_activa", "1") == "1")
        self.dias_limpieza_input.setText(self.config.get("dias_conservar_archivos", "30"))
        self.print_jobs_pc_activos_check.setChecked(
            self.config.get("pc_print_jobs_activos", "1") == "1"
        )
        self.cargar_impresoras_en_combo()
        self.actualizar_trabajos_impresion_fallidos()
        self.actualizar_trabajos_impresion_impresos()
        QMessageBox.information(self, "Actualizado", "Configuración recargada desde la base de datos.")

    def actualizar_trabajos_impresion_fallidos(self):
        try:
            trabajos = listar_trabajos_impresion_fallidos()
        except Exception as e:
            self.tabla_trabajos_fallidos.setRowCount(0)
            QMessageBox.warning(self, "Trabajos de impresión", f"No se pudieron cargar los trabajos fallidos:\n{e}")
            return

        self.tabla_trabajos_fallidos.setRowCount(len(trabajos))
        for fila, trabajo in enumerate(trabajos):
            intentos = f"{trabajo['intentos']}/{trabajo['max_intentos']}"
            valores = [
                trabajo["id"],
                trabajo["tipo"],
                trabajo["destino"] or "-",
                trabajo["patente"] or "-",
                trabajo["estado"],
                intentos,
                trabajo["updated_at"],
                trabajo["last_error"] or "-",
            ]
            for columna, valor in enumerate(valores):
                item = QTableWidgetItem(str(valor))
                if columna == 7:
                    item.setToolTip(str(valor))
                self.tabla_trabajos_fallidos.setItem(fila, columna, item)

    def reintentar_trabajo_impresion_seleccionado(self):
        fila = self.tabla_trabajos_fallidos.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Trabajos de impresión", "Selecciona un trabajo fallido para reintentar.")
            return

        id_trabajo = int(self.tabla_trabajos_fallidos.item(fila, 0).text())
        estado = self.tabla_trabajos_fallidos.item(fila, 4).text()
        if estado == "REVISION_MANUAL":
            mensaje = (
                f"El ticket #{id_trabajo} pudo haberse enviado o impreso. "
                "Verificá físicamente antes de reintentar para evitar un duplicado.\n\n"
                "¿Deseás dejarlo pendiente para reintento?"
            )
        else:
            mensaje = f"¿Deseas reintentar el trabajo de impresión #{id_trabajo}?"
        confirmar = QMessageBox.question(
            self,
            "Confirmar reintento",
            mensaje,
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirmar != QMessageBox.Yes:
            return

        try:
            if estado == "REVISION_MANUAL":
                reintentado = reintentar_trabajo_impresion_revision_manual(id_trabajo)
            else:
                reintentado = reintentar_trabajo_impresion_fallido(id_trabajo)
        except Exception as e:
            QMessageBox.critical(self, "Trabajos de impresión", f"No se pudo reintentar el trabajo:\n{e}")
            return

        if not reintentado:
            QMessageBox.warning(
                self,
                "Trabajos de impresión",
                f"El trabajo ya no está en estado {estado} y no se reintentó.",
            )
            self.actualizar_trabajos_impresion_fallidos()
            return

        self.actualizar_trabajos_impresion_fallidos()
        QMessageBox.information(
            self,
            "Trabajos de impresión",
            f"El trabajo #{id_trabajo} quedó pendiente para reintento.",
        )

    def actualizar_trabajos_impresion_impresos(self):
        try:
            trabajos = listar_trabajos_impresion_impresos()
        except Exception as e:
            self.tabla_trabajos_impresos.setRowCount(0)
            QMessageBox.warning(self, "Trabajos de impresión", f"No se pudieron cargar los trabajos impresos:\n{e}")
            return

        self.tabla_trabajos_impresos.setRowCount(len(trabajos))
        for fila, trabajo in enumerate(trabajos):
            valores = [
                trabajo["id"],
                trabajo["tipo"],
                trabajo["destino"] or "-",
                trabajo["patente"] or "-",
                trabajo["estado"],
                trabajo["updated_at"],
            ]
            for columna, valor in enumerate(valores):
                self.tabla_trabajos_impresos.setItem(fila, columna, QTableWidgetItem(str(valor)))

    def reimprimir_trabajo_impresion_seleccionado(self):
        fila = self.tabla_trabajos_impresos.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Trabajos de impresión", "Selecciona un trabajo impreso para reimprimir.")
            return

        id_trabajo = int(self.tabla_trabajos_impresos.item(fila, 0).text())
        motivo, aceptado = QInputDialog.getText(
            self,
            "Motivo de reimpresión",
            f"Indica el motivo para reimprimir el trabajo #{id_trabajo}:",
        )
        motivo = motivo.strip()
        if not aceptado:
            return
        if not motivo:
            QMessageBox.warning(self, "Motivo obligatorio", "Debes indicar un motivo para reimprimir.")
            return

        confirmar = QMessageBox.question(
            self,
            "Confirmar reimpresión",
            f"Se creará un nuevo trabajo pendiente para reimprimir el ticket #{id_trabajo}.\n\n"
            "Verificá físicamente antes de continuar para evitar un duplicado.\n\n"
            "¿Deseás continuar?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirmar != QMessageBox.Yes:
            return

        try:
            resultado = crear_reimpresion_trabajo_impresion(id_trabajo, self.usuario, motivo)
        except ValueError as e:
            QMessageBox.warning(self, "Reimpresión", str(e))
            return
        except Exception as e:
            QMessageBox.critical(self, "Reimpresión", f"No se pudo crear la reimpresión:\n{e}")
            return

        if resultado is False:
            QMessageBox.warning(
                self,
                "Reimpresión",
                "Ya existe una reimpresión pendiente o en revisión para este ticket.",
            )
            self.actualizar_trabajos_impresion_impresos()
            return

        if resultado is None:
            QMessageBox.warning(
                self,
                "Reimpresión",
                "El trabajo ya no está en estado IMPRESO y no se creó una reimpresión.",
            )
            self.actualizar_trabajos_impresion_impresos()
            return

        self.actualizar_trabajos_impresion_impresos()
        QMessageBox.information(
            self,
            "Reimpresión creada",
            f"El nuevo trabajo #{resultado['new_print_job_id']} quedó pendiente de impresión.",
        )

    def cargar_impresoras_en_combo(self):
        """
        Carga las impresoras instaladas en el QComboBox y selecciona
        la guardada o la predeterminada si corresponde.
        """
        self.impresora_combo.clear()

        impresoras = obtener_impresoras_instaladas()
        if not impresoras:
            self.impresora_combo.addItem("No hay impresoras disponibles")
            self.impresora_combo.setEnabled(False)
            self.btn_guardar_impresora.setEnabled(False)
            self.btn_probar_impresion.setEnabled(False)
            return

        self.impresora_combo.setEnabled(True)
        self.btn_guardar_impresora.setEnabled(True)
        self.btn_probar_impresion.setEnabled(True)

        self.impresora_combo.addItems(impresoras)

        impresora_guardada = cargar_impresora_guardada()
        impresora_default = obtener_impresora_predeterminada()

        if impresora_guardada and impresora_guardada in impresoras:
            self.impresora_combo.setCurrentText(impresora_guardada)
        elif impresora_default and impresora_default in impresoras:
            self.impresora_combo.setCurrentText(impresora_default)

    def guardar_impresora_seleccionada(self):
        """
        Guarda la impresora actualmente seleccionada en config.ini.
        """
        impresora = self.impresora_combo.currentText().strip()

        if not impresora or impresora == "No hay impresoras disponibles":
            QMessageBox.warning(
                self,
                "Error",
                "No hay una impresora válida para guardar."
            )
            return

        guardar_impresora_tickets(impresora)
        QMessageBox.information(
            self,
            "Guardado",
            f"Impresora de tickets guardada correctamente:\n{impresora}"
        )

    def probar_impresion_ticket(self):
        """
        Genera y envía una prueba local a la impresora seleccionada.

        This intentionally bypasses print_jobs because it is an explicit
        hardware check, never an operational receipt.
        """
        impresora = self.impresora_combo.currentText().strip()

        if not impresora or impresora == "No hay impresoras disponibles":
            QMessageBox.warning(
                self,
                "Error",
                "No hay una impresora válida seleccionada."
            )
            return

        try:
            carpeta = Path("tickets")
            carpeta.mkdir(exist_ok=True)

            ruta_pdf = carpeta / "ticket_prueba_impresora.pdf"

            pdf = FPDF(format=(58, 90), unit="mm")
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=4)
            pdf.set_font("Courier", size=9)

            pdf.cell(0, 5, "ESTACIONAMIENTO CENTRAL", ln=True, align="C")
            pdf.cell(0, 5, "Ticket de Prueba", ln=True, align="C")
            pdf.cell(0, 4, "-" * 28, ln=True, align="C")
            pdf.cell(0, 5, f"Impresora:", ln=True)
            pdf.multi_cell(0, 5, impresora)
            pdf.cell(0, 5, "Estado: prueba correcta", ln=True)
            pdf.cell(0, 5, "Gracias por su visita", ln=True, align="C")

            pdf.output(str(ruta_pdf))

            ruta_sumatra = next(
                (
                    ruta
                    for ruta in (
                        Path(r"C:\Program Files\SumatraPDF\SumatraPDF.exe"),
                        Path(r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe"),
                        Path.home() / r"AppData\Local\SumatraPDF\SumatraPDF.exe",
                    )
                    if ruta.is_file()
                ),
                None,
            )
            if not ruta_sumatra:
                raise FileNotFoundError("No se encontró SumatraPDF en rutas conocidas.")

            subprocess.Popen(
                [
                    str(ruta_sumatra),
                    "-print-to", impresora,
                    "-silent",
                    "-exit-on-print",
                    str(ruta_pdf),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            QMessageBox.information(
                self,
                "Prueba enviada",
                f"Se envió un ticket de prueba a:\n{impresora}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error de impresión",
                f"Ocurrió un error al generar o imprimir el ticket de prueba:\n{e}"
            )

    def guardar(self):
        modo = self.modo_combo.currentText()
        tarifa_minima = self.minima_input.text().strip()
        valor_minuto = self.minuto_input.text().strip()
        tarifa_hora = self.hora_input.text().strip()
        valor_bano = self.bano_input.text().strip()
        noches_valor = self.noches_valor_input.text().strip()
        valores_lavado = {
            clave: input_valor.text().strip()
            for clave, input_valor in self.lavado_inputs.items()
        }
        dias_limpieza = self.dias_limpieza_input.text().strip()

        if (
            not tarifa_minima.isdigit() 
            or not valor_minuto.isdigit() 
            or not tarifa_hora.isdigit() 
            or not valor_bano.isdigit()
            or not noches_valor.isdigit()
            or any(not valor.isdigit() for valor in valores_lavado.values())
            or not dias_limpieza.isdigit()
        ):
            QMessageBox.warning(self, "Error", "Tarifas, valores de lavado, noches y días de limpieza deben ser números enteros.")
            return

        actualizar_configuracion("modo_cobro", modo)
        actualizar_configuracion("tarifa_minima", tarifa_minima)
        actualizar_configuracion("tarifa_hora", tarifa_hora)
        actualizar_configuracion("valor_minuto", valor_minuto)
        actualizar_configuracion("valor_bano", valor_bano)
        actualizar_configuracion("noches_activo", 1 if self.noches_activo_check.isChecked() else 0)
        actualizar_configuracion("noches_valor", noches_valor)
        for clave, valor in valores_lavado.items():
            actualizar_configuracion(clave, valor)
        actualizar_configuracion("limpieza_automatica_activa", 1 if self.limpieza_activa_check.isChecked() else 0)
        actualizar_configuracion("dias_conservar_archivos", dias_limpieza)
        actualizar_configuracion(
            "pc_print_jobs_activos",
            1 if self.print_jobs_pc_activos_check.isChecked() else 0,
        )

        QMessageBox.information(self, "Guardado", "Configuración actualizada correctamente.")

    def generar_tramos_auto(self):
        confirmar = QMessageBox.question(
            self,
            "Confirmación",
            "¿Deseas generar automáticamente los tramos de tarifas personalizados?\nEsto sobrescribirá los tramos actuales.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirmar != QMessageBox.Yes:
            return

        try:
            resultado = generar_tramos_automaticos()
            actualizar_configuracion("modo_auto_simplificado", 1)

            if callable(self.on_tramos_actualizados):
                self.on_tramos_actualizados()

            QMessageBox.information(
                self,
                "Éxito",
                resultado["mensaje"]
            )

        except ValueError as e:
            QMessageBox.warning(self, "Configuración inválida", str(e))
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudieron generar los tramos automáticos:\n{e}"
            )
