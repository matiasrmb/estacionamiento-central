from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTableWidget,
    QTableWidgetItem, QGroupBox, QHeaderView, QCompleter,
    QHBoxLayout, QGridLayout, QFrame, QSizePolicy, QScrollArea,
    QDialog, QDialogButtonBox, QInputDialog
)
from PySide6.QtCore import QTimer, Qt, QSize
from PySide6.QtGui import QIcon, QShortcut, QKeySequence
from datetime import datetime, timedelta
from html import escape
from pathlib import Path
import sys
from controllers.registro_controller import (
    buscar_estado_vehiculo, registrar_ingreso_detallado, registrar_ingreso_con_noches_detallado,
    obtener_opcion_noches,
    registrar_salida_detallada, obtener_vehiculos_activos,
    obtener_preview_salida_por_patente,
    obtener_noche_pendiente_por_patente, finalizar_noche_pendiente, convertir_noche_a_ingreso_normal,
    marcar_ingreso_en_espera, alternar_estado_espera, enviar_salida_sin_cobro_a_espera,
    obtener_patentes_existentes, eliminar_ingreso_activo_por_patente,
    registrar_uso_bano, obtener_total_vehiculos_pagados_turno_actual, obtener_resumen_caja_actual,
    obtener_patentes_turno_actual_para_f4, ordenar_patentes_para_busqueda,
    ordenar_patentes_turno_para_f4,
)
from controllers.subida_controller import crear_subida_temporal, obtener_subida_activa
from controllers.config_controller import obtener_configuracion
from controllers.tarifas_controller import calcular_tarifa, describir_detalle_tarifa
from controllers.dashboard_controller import obtener_resumen_banos
from controllers.lavados_controller import (
    finalizar_lavado,
    iniciar_lavado,
    obtener_categorias_lavado,
)
from controllers.operaciones_servicio_controller import (
    finalizar_solo_lavado_cobrando,
    finalizar_solo_lavado_como_estadia,
    iniciar_solo_lavado,
    obtener_solo_lavados_activos,
)
from controllers.wash_pricing_controller import SOLO_LAVADO_PRICE_CONFIG_MESSAGE, list_wash_vehicle_types
from controllers.cotizaciones_controller import (
    calcular_minutos_estadia_por_horarios,
    preview_cotizacion,
    resolve_wash_quote_options,
    wash_quote_options_from_legacy_config,
)
from views.subida_dialog import SubidaDialog
from utils.plates import normalizar_patente, validar_patente
from utils.local_preferences import obtener_modo_privacidad_metricas


def formatear_fecha_hora(valor):
    return valor.strftime("%d/%m/%Y %H:%M")


def formatear_hora(valor):
    if hasattr(valor, "strftime"):
        return valor.strftime("%H:%M")
    try:
        return datetime.strptime(str(valor), "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
    except ValueError:
        return str(valor)


def ruta_recurso(*partes):
    """Resuelve recursos tanto desde el código fuente como desde PyInstaller."""
    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return str(base_dir.joinpath(*partes))


def construir_mensaje_ingreso(ingreso, mensaje="Vehículo ingresado correctamente", detalle=None):
    lineas = [
        escape(mensaje),
        "",
        f"Patente: <b>{escape(str(ingreso['patente']))}</b>",
        f"Ingreso: <b>{escape(formatear_hora(ingreso['fecha_hora_ingreso']))}</b>",
    ]
    if detalle:
        lineas.append(escape(detalle))
    return '<div style="font-size: 14pt;">' + "<br>".join(lineas) + "</div>"


def construir_mensaje_salida(salida):
    lineas = [
        "Salida registrada correctamente",
        "",
        f"Patente: <b>{escape(str(salida['patente']))}</b>",
        f"Ingreso: <b>{escape(formatear_hora(salida['fecha_hora_ingreso']))}</b>",
        f"Salida: <b>{escape(formatear_hora(salida['fecha_hora_salida']))}</b>",
        f"Tiempo cobrado: {salida['minutos']} min",
    ]
    if salida.get("noches_prepagadas"):
        lineas.append(f"Noches ya pagadas: ${salida['total_noches_prepagadas']:.0f}")
    lineas.append(f"A cobrar ahora: <b>${salida['tarifa']:.0f}</b>")
    return '<div style="font-size: 14pt;">' + "<br>".join(lineas) + "</div>"


def _es_tabla_lavado_faltante(exc):
    mensaje = str(exc).lower()
    tablas_lavado = ("tipos_vehiculo_lavado", "tipos_vehiculos_lavado")
    return any(tabla in mensaje for tabla in tablas_lavado) and (
        "doesn't exist" in mensaje or "does not exist" in mensaje or "no such table" in mensaje
    )


REGISTRO_METRICAS = (
    "Vehículos activos",
    "Usos de baño hoy",
    "Estimado activos",
    "Total proyectado",
    "Total turno",
    "Neto en caja",
)
(
    METRICA_VEHICULOS_ACTIVOS,
    METRICA_USOS_BANO,
    METRICA_ESTIMADO_ACTIVOS,
    METRICA_TOTAL_PROYECTADO,
    METRICA_TOTAL_TURNO,
    METRICA_NETO_CAJA,
) = REGISTRO_METRICAS


def calcular_metricas_resumen(total_activos, resumen_caja):
    """Calcula los importes de las tarjetas sin mezclar estimaciones con cobros."""
    total_turno = float(resumen_caja["total_general"])
    return {
        "estimado_activos": float(total_activos),
        "total_proyectado": total_turno + float(total_activos),
        "total_turno": total_turno,
        "neto_caja": float(resumen_caja["total_neto"]),
    }


class TarjetaResumen(QFrame):
    """Tarjeta de métrica que revela su valor al pasar el mouse en modo privacidad."""

    def __init__(self, titulo, valor, icono_archivo, ayuda=None, modo_privacidad=False):
        super().__init__()
        self.setObjectName("ResumenModulo")
        self.setFixedHeight(112)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMouseTracking(True)
        self.valor_real = valor
        self.modo_privacidad = modo_privacidad
        self.mouse_sobre_tarjeta = False
        self.icono_archivo = icono_archivo
        self.icono = QIcon(ruta_recurso("assets", "icons", icono_archivo))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        encabezado = QHBoxLayout()
        encabezado.setSpacing(6)
        self.label_icono = QLabel()
        self.label_icono.setObjectName("IconoResumenModulo")
        self.label_icono.setPixmap(self.icono.pixmap(QSize(22, 22)))
        self.label_titulo = QLabel(titulo)
        self.label_titulo.setObjectName("TituloResumenModulo")
        self.label_titulo.setWordWrap(True)
        self.label_titulo.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.label_titulo.setToolTip(ayuda or titulo)
        encabezado.addWidget(self.label_icono, 0, alignment=Qt.AlignTop)
        encabezado.addWidget(self.label_titulo, 1, alignment=Qt.AlignTop)
        if ayuda:
            self.label_ayuda = QLabel("i")
            self.label_ayuda.setObjectName("AyudaResumenModulo")
            self.label_ayuda.setToolTip(ayuda)
            self.label_ayuda.setFixedSize(16, 16)
            self.label_ayuda.setAlignment(Qt.AlignCenter)
            encabezado.addWidget(self.label_ayuda, 0, alignment=Qt.AlignTop)

        self.label_valor = QLabel()
        self.label_valor.setObjectName("ValorResumenModulo")
        self.label_valor.setWordWrap(True)
        self.label_privacidad = QLabel()
        self.label_privacidad.setObjectName("IconoPrivacidadResumenModulo")
        self.label_privacidad.setAlignment(Qt.AlignCenter)
        self.label_privacidad.setPixmap(self.icono.pixmap(QSize(36, 36)))
        layout.addLayout(encabezado)
        layout.addWidget(self.label_valor)
        layout.addWidget(self.label_privacidad)
        self.actualizar_valor_visible()

    def set_valor(self, valor):
        self.valor_real = valor
        self.actualizar_valor_visible()

    def set_modo_privacidad(self, activo):
        self.modo_privacidad = activo
        self.actualizar_valor_visible()

    def actualizar_valor_visible(self, revelar=False):
        revelar = revelar or self.mouse_sobre_tarjeta
        valor_visible = not self.modo_privacidad or revelar
        self.label_valor.setText(self.valor_real if valor_visible else "")
        self.label_valor.setVisible(valor_visible)
        self.label_icono.setVisible(valor_visible)
        self.label_privacidad.setVisible(self.modo_privacidad and not revelar)

    def enterEvent(self, event):
        self.mouse_sobre_tarjeta = True
        self.actualizar_valor_visible()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.mouse_sobre_tarjeta = False
        self.actualizar_valor_visible()
        super().leaveEvent(event)


class RegistroWindow(QWidget):
    """
    Vista principal para el registro de ingresos y salidas de vehículos.
    """

    def __init__(self, usuario, rol="operador", on_volver_panel=None, on_ir_edicion=None):
        super().__init__()
        self.usuario = usuario
        self.rol = rol
        self.on_volver_panel = on_volver_panel
        self.on_ir_edicion = on_ir_edicion
        self.panel_secundario_expandido = True
        self.patentes_f3 = []
        self.indice_patente_f3 = -1
        self.busqueda_f3 = ""
        self.patentes_f4 = []
        self.indice_patente_f4 = -1
        self.busqueda_f4 = ""
        self.seleccion_f4 = None
        self.modo_privacidad_metricas = obtener_modo_privacidad_metricas()

        self.setMinimumSize(1000, 650)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # =========================================================
        # ENCABEZADO
        # =========================================================
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self.boton_volver = QPushButton("Volver al panel principal")
        self.boton_volver.setObjectName("BotonSecundario")
        self.boton_volver.setMinimumHeight(38)
        self.boton_volver.clicked.connect(self.volver_al_panel)

        self.boton_actualizar_pantalla = QPushButton("Actualizar pantalla")
        self.boton_actualizar_pantalla.setObjectName("BotonSecundario")
        self.boton_actualizar_pantalla.setMinimumHeight(38)
        self.boton_actualizar_pantalla.clicked.connect(self.actualizar_pantalla)

        header_layout.addWidget(self.boton_volver, 0, alignment=Qt.AlignLeft)
        header_layout.addStretch(1)
        header_layout.addWidget(self.boton_actualizar_pantalla, 0, alignment=Qt.AlignRight)

        layout.addLayout(header_layout)

        # =========================================================
        # BLOQUE SUPERIOR
        # =========================================================
        superior_layout = QGridLayout()
        superior_layout.setHorizontalSpacing(12)
        superior_layout.setVerticalSpacing(12)

        # -------- Búsqueda / patente --------
        grupo_busqueda = QGroupBox("Consulta de patente")
        grupo_busqueda.setSizePolicy(grupo_busqueda.sizePolicy().horizontalPolicy(), QSizePolicy.Preferred)
        layout_busqueda = QVBoxLayout()
        layout_busqueda.setContentsMargins(14, 0, 14, 18)
        layout_busqueda.setSpacing(10)

        self.label_patente = QLabel("Patente del vehículo")
        self.label_patente.setObjectName("EtiquetaFormulario")

        self.input_patente = QLineEdit()
        self.input_patente.setObjectName("InputPatente")
        self.input_patente.setPlaceholderText("Ej: ABCD12")
        self.input_patente.setMaxLength(20)
        self.input_patente.setMinimumHeight(42)
        self.input_patente.textChanged.connect(self.normalizar_patente_busqueda)
        self.input_patente.textEdited.connect(self.reiniciar_busqueda_f3)
        self.input_patente.textEdited.connect(self.reiniciar_busqueda_f4)
        self.input_patente.returnPressed.connect(self.buscar_vehiculo)

        patentes = obtener_patentes_existentes()
        self.completer_patentes = QCompleter(patentes, self)
        self.completer_patentes.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer_patentes.setFilterMode(Qt.MatchContains)
        self.input_patente.setCompleter(self.completer_patentes)
        self.completer_patentes.activated.connect(self.seleccionar_patente_autocompletada)

        self.boton_buscar = QPushButton("Buscar estado del vehículo")
        self.boton_buscar.setMinimumHeight(40)
        self.boton_buscar.clicked.connect(self.buscar_vehiculo)

        self.boton_refrescar_patentes = QPushButton("Actualizar lista de patentes")
        self.boton_refrescar_patentes.setObjectName("BotonSecundario")
        self.boton_refrescar_patentes.setMinimumHeight(38)
        self.boton_refrescar_patentes.clicked.connect(self.actualizar_lista_patentes)

        self.info_label = QLabel("Escribe una patente y presiona Enter o el botón de búsqueda.")
        self.info_label.setObjectName("EstadoInfoNeutro")
        self.info_label.setWordWrap(True)
        self.actualizar_estilo_info("neutro")

        self.hora_consulta_label = QLabel("")
        self.hora_consulta_label.setObjectName("PreviewSalida")
        self.hora_consulta_label.setWordWrap(True)
        self.hora_consulta_label.setMinimumHeight(128)

        layout_busqueda.addWidget(self.label_patente)
        layout_busqueda.addWidget(self.input_patente)
        layout_busqueda.addWidget(self.boton_buscar)
        layout_busqueda.addWidget(self.boton_refrescar_patentes)
        layout_busqueda.addWidget(self.info_label)
        layout_busqueda.addWidget(self.hora_consulta_label)
        layout_busqueda.addStretch()

        grupo_busqueda.setLayout(layout_busqueda)

        # -------- Acciones --------
        grupo_acciones = QGroupBox("Acciones principales")
        layout_acciones = QVBoxLayout()
        layout_acciones.setContentsMargins(14, 0, 14, 18)
        layout_acciones.setSpacing(8)

        self.boton_ingreso = QPushButton("Registrar ingreso")
        self.boton_ingreso.setEnabled(False)
        self.boton_ingreso.setMinimumHeight(32)
        self.boton_ingreso.clicked.connect(self.registrar_ingreso)

        self.boton_ingreso_personalizado = QPushButton("Registrar ingreso con hora")
        self.boton_ingreso_personalizado.setEnabled(False)
        self.boton_ingreso_personalizado.setMinimumHeight(32)
        self.boton_ingreso_personalizado.clicked.connect(self.registrar_ingreso_con_hora_personalizada)

        self.boton_ingreso_noches = QPushButton("Registrar ingreso en modo Noche")
        self.boton_ingreso_noches.setEnabled(False)
        self.boton_ingreso_noches.setMinimumHeight(32)
        self.boton_ingreso_noches.clicked.connect(self.registrar_ingreso_con_noches)

        self.boton_salida = QPushButton("Registrar salida")
        self.boton_salida.setEnabled(False)
        self.boton_salida.setMinimumHeight(32)
        self.boton_salida.clicked.connect(self.registrar_salida)

        self.boton_espera = QPushButton("Marcar como en espera")
        self.boton_espera.setEnabled(False)
        self.boton_espera.setMinimumHeight(32)
        self.boton_espera.clicked.connect(self.marcar_en_espera)

        self.boton_bano = QPushButton("Registrar baño")
        self.boton_bano.setMinimumHeight(32)
        self.boton_bano.clicked.connect(self.mostrar_opciones_bano)

        self.boton_lavado = QPushButton("Iniciar/finalizar lavado")
        self.boton_lavado.setMinimumHeight(32)
        self.boton_lavado.clicked.connect(self.alternar_lavado_seleccionado)

        self.boton_solo_lavado = QPushButton("Iniciar solo lavado")
        self.boton_solo_lavado.setMinimumHeight(32)
        self.boton_solo_lavado.clicked.connect(self.iniciar_solo_lavado_desde_patente)

        self.boton_cotizar = QPushButton("Cotizaciones")
        self.boton_cotizar.setMinimumHeight(32)
        self.boton_cotizar.clicked.connect(self.mostrar_cotizacion)

        layout_acciones.addWidget(self.boton_ingreso)
        layout_acciones.addWidget(self.boton_ingreso_personalizado)
        layout_acciones.addWidget(self.boton_ingreso_noches)
        layout_acciones.addWidget(self.boton_salida)
        layout_acciones.addWidget(self.boton_espera)
        layout_acciones.addWidget(self.boton_bano)
        layout_acciones.addWidget(self.boton_lavado)
        layout_acciones.addWidget(self.boton_solo_lavado)
        layout_acciones.addWidget(self.boton_cotizar)

        if self.rol == "administrador":
            self.boton_subida = QPushButton("Subida temporal de precios")
            self.boton_subida.setMinimumHeight(42)
            self.boton_subida.clicked.connect(self.abrir_dialogo_subida)

            layout_acciones.addWidget(self.boton_subida)

        layout_acciones.addStretch()
        grupo_acciones.setLayout(layout_acciones)

        # -------- Panel secundario --------
        self.grupo_estado = QGroupBox("Información adicional")
        layout_estado_principal = QVBoxLayout()
        layout_estado_principal.setContentsMargins(14, 0, 14, 18)
        layout_estado_principal.setSpacing(10)

        header_estado = QHBoxLayout()
        header_estado.setSpacing(8)

        self.label_estado_titulo = QLabel("Estado y atajos")
        self.label_estado_titulo.setObjectName("EtiquetaFormulario")

        self.btn_toggle_panel = QPushButton("Ocultar")
        self.btn_toggle_panel.setObjectName("BotonSecundario")
        self.btn_toggle_panel.setMinimumHeight(34)
        self.btn_toggle_panel.clicked.connect(self.toggle_panel_secundario)

        header_estado.addWidget(self.label_estado_titulo)
        header_estado.addStretch()
        header_estado.addWidget(self.btn_toggle_panel)

        self.panel_secundario = QWidget()
        panel_secundario_layout = QVBoxLayout(self.panel_secundario)
        panel_secundario_layout.setContentsMargins(0, 0, 0, 0)
        panel_secundario_layout.setSpacing(10)

        self.label_usuario_activo = QLabel(f"Usuario: {self.usuario} ({self.rol})")
        self.label_usuario_activo.setWordWrap(True)

        self.label_subida = QLabel("Subida temporal: no activa")
        self.label_subida.setWordWrap(True)

        self.label_atajos = QLabel(
            "Atajos rápidos:\n"
            "Enter: buscar patente\n"
            "F1: ingresar o salir\n"
            "F2 o ESC: limpiar formulario\n"
            "F3: buscar/recorrer patentes abiertas\n"
            "F4: recorrer patentes del turno\n"
            "F6: registrar baño\n"
            "F7: reingresar vehículo\n"
            "F8: alternar espera\n"
            "F9: eliminar ingreso en espera\n"
            "F10: consultar tarifa\n"
            "F11: ingresar con hora personalizada\n"
            "Ctrl+L: iniciar/finalizar lavado seleccionado"
        )
        self.label_atajos.setWordWrap(True)
        self.label_atajos.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.label_atajos.setStyleSheet("font-size: 12px;")

        self.scroll_atajos = QScrollArea()
        self.scroll_atajos.setWidgetResizable(True)
        self.scroll_atajos.setFrameShape(QFrame.NoFrame)
        self.scroll_atajos.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_atajos.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_atajos.setMinimumHeight(120)

        contenedor_atajos = QWidget()
        layout_atajos = QVBoxLayout(contenedor_atajos)
        layout_atajos.setContentsMargins(0, 8, 0, 50)
        layout_atajos.setSpacing(0)
        layout_atajos.addWidget(self.label_atajos)
        layout_atajos.addStretch()

        self.scroll_atajos.setWidget(contenedor_atajos)

        panel_secundario_layout.addWidget(self.label_usuario_activo)
        panel_secundario_layout.addWidget(self.label_subida)
        panel_secundario_layout.addWidget(self.scroll_atajos, 1)

        layout_estado_principal.addLayout(header_estado)
        layout_estado_principal.addWidget(self.panel_secundario)
        self.grupo_estado.setLayout(layout_estado_principal)

        superior_layout.addWidget(grupo_busqueda, 0, 0)
        superior_layout.addWidget(grupo_acciones, 0, 1)
        superior_layout.addWidget(self.grupo_estado, 0, 2)

        superior_layout.setColumnStretch(0, 3)
        superior_layout.setColumnStretch(1, 3)
        superior_layout.setColumnStretch(2, 2)

        layout.addLayout(superior_layout, 0)

        # =========================================================
        # RESUMEN
        # =========================================================
        resumen_layout = QHBoxLayout()
        resumen_layout.setSpacing(12)

        self.card_estacionados = self.crear_tarjeta_resumen(
            METRICA_VEHICULOS_ACTIVOS, "0", "vehiculos-activos.svg"
        )
        self.card_banos = self.crear_tarjeta_resumen(
            METRICA_USOS_BANO, "0", "usos-bano-hoy.svg"
        )
        self.card_total_activos = self.crear_tarjeta_resumen(
            METRICA_ESTIMADO_ACTIVOS, "$0", "estimado-activos.svg", "Vehículos sin cobrar"
        )
        self.card_total_proyectado = self.crear_tarjeta_resumen(
            METRICA_TOTAL_PROYECTADO, "$0", "total-proyectado.svg", "Cobrado + activos estimados"
        )
        self.card_total_turno = self.crear_tarjeta_resumen(
            METRICA_TOTAL_TURNO, "$0", "total-turno.svg", "Cobrado desde último cierre"
        )
        self.card_neto_caja = self.crear_tarjeta_resumen(
            METRICA_NETO_CAJA, "$0", "neto-caja.svg", "Cobrado - gastos"
        )

        resumen_layout.addWidget(self.card_estacionados)
        resumen_layout.addWidget(self.card_banos)
        resumen_layout.addWidget(self.card_total_activos)
        resumen_layout.addWidget(self.card_total_proyectado)
        resumen_layout.addWidget(self.card_total_turno)
        resumen_layout.addWidget(self.card_neto_caja)
        resumen_layout.addStretch()

        layout.addLayout(resumen_layout)

        # =========================================================
        # TABLA
        # =========================================================
        self.grupo_tabla = QGroupBox("Vehículos actualmente estacionados")
        self.grupo_tabla.setVisible(False)
        self.grupo_tabla.setMinimumHeight(240)
        self.grupo_tabla.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout_tabla = QVBoxLayout()
        layout_tabla.setContentsMargins(10, 0, 10, 16)
        layout_tabla.setSpacing(8)

        self.tabla_activos = QTableWidget()
        self.tabla_activos.setObjectName("TablaActivos")
        self.tabla_activos.setColumnCount(4)
        self.tabla_activos.setHorizontalHeaderLabels(["Patente", "Hora ingreso", "Minutos", "Monto actual"])
        self.tabla_activos.setMinimumHeight(200)
        self.tabla_activos.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tabla_activos.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tabla_activos.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_activos.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla_activos.verticalHeader().setDefaultSectionSize(36)
        self.tabla_activos.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        self.tabla_activos.setAutoScroll(False)

        self.tabla_activos.horizontalHeader().setStretchLastSection(False)
        self.tabla_activos.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla_activos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla_activos.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabla_activos.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

        self.tabla_activos.cellDoubleClicked.connect(self.cargar_patente_desde_tabla)
        self.tabla_activos.verticalScrollBar().valueChanged.connect(
            self.actualizar_visibilidad_header_tabla
        )

        self.label_leyenda_tabla = QLabel(
            "▲ indica que existe una subida temporal vigente para los vehículos mostrados."
        )
        self.label_leyenda_tabla.setObjectName("LeyendaTabla")
        self.label_leyenda_tabla.setWordWrap(True)

        layout_tabla.addWidget(self.tabla_activos, 1)
        layout_tabla.addWidget(self.label_leyenda_tabla, 0, alignment=Qt.AlignLeft)
        layout_tabla.setStretch(0, 1)
        layout_tabla.setStretch(1, 0)

        self.grupo_tabla.setLayout(layout_tabla)
        layout.addWidget(self.grupo_tabla, 1)

        # =========================================================
        # TIMERS / ESTADO INICIAL
        # =========================================================
        self.timer_tabla = QTimer()
        self.timer_tabla.timeout.connect(self.actualizar_tabla_activos)
        self.timer_tabla.timeout.connect(self.actualizar_estado_subida)
        self.timer_tabla.start(5000)

        self.actualizar_tabla_activos()
        self.actualizar_lista_patentes()
        self.actualizar_estado_subida()
        self.actualizar_visibilidad_header_tabla()

        self.setLayout(layout)

        self.configurar_atajos()

        QTimer.singleShot(0, self.input_patente.setFocus)

    def crear_tarjeta_resumen(self, titulo, valor, icono, ayuda=None):
        return TarjetaResumen(
            titulo,
            valor,
            icono,
            ayuda,
            modo_privacidad=self.modo_privacidad_metricas,
        )

    def toggle_panel_secundario(self):
        self.panel_secundario_expandido = not self.panel_secundario_expandido
        self.panel_secundario.setVisible(self.panel_secundario_expandido)
        self.btn_toggle_panel.setText("Ocultar" if self.panel_secundario_expandido else "Mostrar")

    def volver_al_panel(self):
        self.reset()
        if callable(self.on_volver_panel):
            self.on_volver_panel()

    def buscar_vehiculo(self):
        patente = self.input_patente.text().strip().upper()

        self.hora_consulta_label.clear()

        estado = buscar_estado_vehiculo(patente)

        if estado == "no_registrado":
            self.actualizar_estilo_info("ok")
            self.info_label.setText("Vehículo no registrado. Puedes crear su ingreso.")
            self.boton_ingreso.setEnabled(True)
            self.boton_ingreso_personalizado.setEnabled(True)
            self.boton_ingreso_noches.setEnabled(bool(obtener_opcion_noches()))
            self.boton_salida.setEnabled(False)
            self.boton_espera.setEnabled(False)
            self.mostrar_preview_ingreso(patente)

        elif estado == "dentro":
            self.actualizar_estilo_info("warn")
            self.info_label.setText("Vehículo actualmente dentro del estacionamiento. Puedes registrar salida o marcar en espera.")
            self.boton_salida.setEnabled(True)
            self.boton_ingreso.setEnabled(False)
            self.boton_ingreso_personalizado.setEnabled(False)
            self.boton_ingreso_noches.setEnabled(False)
            self.boton_espera.setEnabled(True)
            preview = obtener_preview_salida_por_patente(patente)
            if preview and preview.get("estado") == "dentro":
                self.mostrar_preview_salida(preview)
            elif preview and preview.get("estado") == "en_espera":
                self.hora_consulta_label.setText("VEHÍCULO EN ESPERA\nNo hay vista previa de salida disponible.")
            elif preview and preview.get("estado") == "en_lavado":
                self.hora_consulta_label.setText("VEHÍCULO EN LAVADO\nFinaliza el lavado antes de registrar la salida.")
            elif preview and preview.get("estado") == "noche_pendiente":
                self.hora_consulta_label.setText("NOCHE PENDIENTE\nRevisa la noche: marcar retirado o convertir a ingreso normal desde 10:00.")

        elif estado == "fuera":
            self.actualizar_estilo_info("neutro")
            self.info_label.setText("Vehículo fuera del estacionamiento. Puedes registrar un nuevo ingreso.")
            self.boton_ingreso.setEnabled(True)
            self.boton_ingreso_personalizado.setEnabled(True)
            self.boton_ingreso_noches.setEnabled(bool(obtener_opcion_noches()))
            self.boton_salida.setEnabled(False)
            self.boton_espera.setEnabled(False)
            self.mostrar_preview_ingreso(patente)

        else:
            self.actualizar_estilo_info("error")
            self.info_label.setText("No fue posible determinar el estado del vehículo.")
            self.boton_ingreso.setEnabled(False)
            self.boton_ingreso_personalizado.setEnabled(False)
            self.boton_ingreso_noches.setEnabled(False)
            self.boton_salida.setEnabled(False)
            self.boton_espera.setEnabled(False)
            QMessageBox.critical(self, "Error", "Error al consultar la patente.")
            self.enfocar_patente()

    def formatear_fecha_hora_info(self, valor):
        if not valor:
            return "-"
        if hasattr(valor, "strftime"):
            return formatear_fecha_hora(valor)
        try:
            return formatear_fecha_hora(datetime.strptime(str(valor), "%Y-%m-%d %H:%M:%S"))
        except ValueError:
            return str(valor)

    def formatear_hora_info(self, valor):
        if not valor:
            return "-"
        if hasattr(valor, "strftime"):
            return valor.strftime("%H:%M")
        try:
            return datetime.strptime(str(valor), "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
        except ValueError:
            return str(valor)

    def mostrar_preview_salida(self, preview):
        lineas = [
            "VEHÍCULO DENTRO",
            f"Patente: {preview['patente']}",
            f"Ingreso: {self.formatear_hora_info(preview['fecha_hora_ingreso'])}",
            f"Consulta de salida: {self.formatear_hora_info(preview['fecha_hora_salida'])}",
            f"Tiempo facturable: {preview['minutos']} min",
            f"Estacionamiento: ${preview['tarifa_estacionamiento']:.0f}",
        ]
        if preview["total_lavados"]:
            lineas.append(f"Lavados: ${preview['total_lavados']:.0f}")
        for cobro in preview.get("noches_prepagadas", []):
            lineas.append(f"Noche pagada: ${cobro['monto_snapshot']:.0f}")
            lineas.append(f"Ventana Noche: {cobro['hora_inicio_snapshot']} a {cobro['hora_fin_snapshot']}")
        if preview.get("minutos_extra_antes_noche"):
            lineas.append(f"Extra antes de noche: {preview['minutos_extra_antes_noche']} min")
        if preview.get("minutos_extra_despues_noche"):
            lineas.append(f"Extra después de noche: {preview['minutos_extra_despues_noche']} min")
        lineas.extend([
            f"A COBRAR AHORA: ${preview['tarifa']:.0f}",
            "El importe se recalcula al registrar la salida.",
        ])
        self.hora_consulta_label.setText("\n".join(lineas))
        self.hora_consulta_label.setObjectName("PreviewSalida")
        self.hora_consulta_label.style().unpolish(self.hora_consulta_label)
        self.hora_consulta_label.style().polish(self.hora_consulta_label)
        self.hora_consulta_label.update()

    def mostrar_preview_ingreso(self, patente):
        ahora = datetime.now()
        self.hora_consulta_label.setText("\n".join([
            "NUEVO INGRESO",
            f"Patente: {patente}",
            f"Hora de ingreso: {self.formatear_hora_info(ahora)}",
            "El ingreso se registra al confirmar la operación.",
        ]))
        self.hora_consulta_label.setObjectName("PreviewSalida")
        self.hora_consulta_label.style().unpolish(self.hora_consulta_label)
        self.hora_consulta_label.style().polish(self.hora_consulta_label)
        self.hora_consulta_label.update()

    def mostrar_info_patente_navegada(
        self,
        tecla,
        posicion,
        total,
        patente,
        estado,
        ingreso,
        salida,
        minutos,
        monto,
    ):
        self.hora_consulta_label.setText(
            f"{tecla} {posicion}/{total} | {patente} | {estado}\n"
            f"Ingreso: {ingreso} | Salida: {salida}\n"
            f"Tiempo: {minutos} min | Monto: ${monto:.0f}"
        )

        if "CERRADO" in estado:
            self.hora_consulta_label.setObjectName("EstadoInfoOk")
        elif "LAVADO" in estado or "ESPERA" in estado:
            self.hora_consulta_label.setObjectName("EstadoInfoWarn")
        else:
            self.hora_consulta_label.setObjectName("EstadoInfoNeutro")

        self.hora_consulta_label.style().unpolish(self.hora_consulta_label)
        self.hora_consulta_label.style().polish(self.hora_consulta_label)
        self.hora_consulta_label.update()

    def seleccionar_siguiente_patente_abierta(self):
        try:
            activos = obtener_vehiculos_activos()
        except Exception as e:
            self.actualizar_estilo_info("error")
            self.info_label.setText("No se pudieron consultar las patentes abiertas.")
            QMessageBox.critical(self, "Error", f"No se pudieron consultar las patentes abiertas:\n{e}")
            return

        patentes = ordenar_patentes_para_busqueda(
            [{
                **activo,
                "patente": activo.get("patente_base") or str(activo.get("patente", "")).split()[0],
            } for activo in activos],
            self.busqueda_f3,
            campo_fecha="hora",
        )
        if not patentes:
            self.actualizar_estilo_info("neutro")
            self.info_label.setText("No hay patentes abiertas que coincidan con la búsqueda.")
            return

        if patentes != self.patentes_f3:
            self.patentes_f3 = patentes
            self.indice_patente_f3 = -1

        self.indice_patente_f3 = (self.indice_patente_f3 + 1) % len(self.patentes_f3)
        seleccion = self.patentes_f3[self.indice_patente_f3]
        patente = str(seleccion.get("patente_base") or seleccion["patente"]).split()[0].upper()

        self.input_patente.setText(patente)
        self.enfocar_patente()
        self.buscar_vehiculo()

        ingreso = self.formatear_fecha_hora_info(seleccion.get("hora"))
        minutos = int(seleccion.get("minutos") or 0)
        monto = float(seleccion.get("monto") or 0)
        extras = []
        if seleccion.get("en_espera"):
            extras.append("EN ESPERA")
        if seleccion.get("en_lavado"):
            extras.append("EN LAVADO")
        estado = "ABIERTO" + (f" ({', '.join(extras)})" if extras else "")

        self.mostrar_info_patente_navegada(
            tecla="F3",
            posicion=self.indice_patente_f3 + 1,
            total=len(self.patentes_f3),
            patente=patente,
            estado=estado,
            ingreso=ingreso,
            salida="Aún dentro",
            minutos=minutos,
            monto=monto,
        )

    def seleccionar_siguiente_patente_turno(self):
        try:
            patentes = obtener_patentes_turno_actual_para_f4()
        except Exception as e:
            self.actualizar_estilo_info("error")
            self.info_label.setText("No se pudieron consultar las patentes del turno.")
            QMessageBox.critical(self, "Error", f"No se pudieron consultar las patentes del turno:\n{e}")
            return

        patentes = ordenar_patentes_turno_para_f4(patentes, self.busqueda_f4)
        if not patentes:
            self.actualizar_estilo_info("neutro")
            self.info_label.setText("No hay patentes del turno que coincidan con la búsqueda.")
            return

        if patentes != self.patentes_f4:
            self.patentes_f4 = patentes
            self.indice_patente_f4 = -1

        self.indice_patente_f4 = (self.indice_patente_f4 + 1) % len(self.patentes_f4)
        seleccion = self.patentes_f4[self.indice_patente_f4]
        self.seleccion_f4 = seleccion
        patente = str(seleccion["patente"]).upper()

        self.input_patente.setText(patente)
        self.enfocar_patente()
        self.buscar_vehiculo()

        ingreso = self.formatear_fecha_hora_info(seleccion.get("fecha_hora_ingreso"))
        salida = self.formatear_fecha_hora_info(seleccion.get("fecha_hora_salida"))
        estado = seleccion.get("estado", "-")
        minutos = int(seleccion.get("minutos") or 0)
        monto = float(seleccion.get("monto") or 0)
        if estado == "ABIERTO" and salida == "-":
            salida = "Aún dentro"

        self.mostrar_info_patente_navegada(
            tecla="F4",
            posicion=self.indice_patente_f4 + 1,
            total=len(self.patentes_f4),
            patente=patente,
            estado=estado,
            ingreso=ingreso,
            salida=salida,
            minutos=minutos,
            monto=monto,
        )

    def registrar_ingreso(self):
        patente = normalizar_patente(self.input_patente.text())

        es_valida, mensaje = self.validar_patente(patente)
        if not es_valida:
            self.actualizar_estilo_info("warn")
            self.info_label.setText(mensaje)
            QMessageBox.warning(self, "Atención", mensaje)
            self.enfocar_patente()
            return

        ingreso = registrar_ingreso_detallado(patente)
        if ingreso:
            QMessageBox.information(
                self,
                "Ingreso registrado",
                construir_mensaje_ingreso(ingreso)
            )
            self.actualizar_lista_patentes()
            self.reset()
        else:
            self.actualizar_estilo_info("error")
            self.info_label.setText("No se pudo registrar el ingreso.")
            QMessageBox.critical(self, "Error", "No se pudo registrar el ingreso.")
            self.enfocar_patente()

        self.actualizar_tabla_activos()

    def registrar_ingreso_con_hora_personalizada(self):
        if not self.boton_ingreso_personalizado.isEnabled():
            QMessageBox.information(
                self,
                "Sin acción",
                "Busca una patente disponible para registrar un ingreso con hora personalizada."
            )
            return

        patente = normalizar_patente(self.input_patente.text())

        es_valida, mensaje = self.validar_patente(patente)
        if not es_valida:
            self.actualizar_estilo_info("warn")
            self.info_label.setText(mensaje)
            QMessageBox.warning(self, "Atención", mensaje)
            self.enfocar_patente()
            return

        dialogo = QDialog(self)
        dialogo.setWindowTitle("Ingreso con hora personalizada")

        layout = QVBoxLayout(dialogo)
        layout.addWidget(QLabel("Ingresa la hora de ingreso de hoy:"))

        input_hora = QLineEdit(dialogo)
        input_hora.setInputMask("00:00;_")
        input_hora.setPlaceholderText("HH:MM")
        input_hora.setMinimumHeight(36)
        input_hora.setAlignment(Qt.AlignCenter)
        layout.addWidget(input_hora)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialogo)
        botones.accepted.connect(dialogo.accept)
        botones.rejected.connect(dialogo.reject)
        layout.addWidget(botones)

        if dialogo.exec() != QDialog.Accepted:
            return

        hora_texto = input_hora.text().strip()
        try:
            hora_personalizada = datetime.strptime(hora_texto, "%H:%M").time()
        except ValueError:
            mensaje = "Formato inválido. Completa la hora con 4 números, por ejemplo 1430."
            self.actualizar_estilo_info("warn")
            self.info_label.setText(mensaje)
            QMessageBox.warning(self, "Hora inválida", mensaje)
            return

        ahora = datetime.now()
        fecha_hora_ingreso = datetime.combine(ahora.date(), hora_personalizada)

        ingreso = registrar_ingreso_detallado(patente, fecha_hora_ingreso)
        if ingreso:
            QMessageBox.information(
                self,
                "Ingreso registrado",
                construir_mensaje_ingreso(ingreso, "Vehículo ingresado correctamente con hora personalizada")
            )
            self.actualizar_lista_patentes()
            self.reset()
        else:
            self.actualizar_estilo_info("error")
            mensaje = "No se pudo registrar el ingreso. La hora debe ser de hoy, no futura y no superar 4 horas de antigüedad."
            self.info_label.setText(mensaje)
            QMessageBox.critical(self, "Error", mensaje)
            self.enfocar_patente()

        self.actualizar_tabla_activos()

    def registrar_ingreso_con_noches(self):
        patente = normalizar_patente(self.input_patente.text())
        es_valida, mensaje = self.validar_patente(patente)
        if not es_valida:
            self.actualizar_estilo_info("warn")
            self.info_label.setText(mensaje)
            QMessageBox.warning(self, "Atención", mensaje)
            self.enfocar_patente()
            return
        opcion = obtener_opcion_noches()
        if not opcion:
            QMessageBox.warning(
                self,
                "Noches no disponible",
                "Noches no está disponible para este ingreso. Verifica que esté habilitado y tenga un valor mayor que cero.",
            )
            return

        confirmacion = QMessageBox.question(
            self,
            "Confirmar ingreso en modo Noche",
            f"Registrar ingreso para {patente} en modo Noche por ${opcion['monto_snapshot']}\n"
            f"Ventana base: {opcion['hora_inicio_snapshot']} a {opcion['hora_fin_snapshot']} (gracia 19:00 a 10:00)",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirmacion != QMessageBox.Yes:
            return

        ingreso = registrar_ingreso_con_noches_detallado(patente, self.usuario)
        if ingreso:
            cobro = ingreso["cobro_noche"]
            QMessageBox.information(
                self,
                "Ingreso registrado",
                construir_mensaje_ingreso(
                    ingreso,
                    "Vehículo ingresado en modo Noche.",
                    f"Noche pagada: ${cobro['monto_snapshot']} ({cobro['hora_inicio_snapshot']} a {cobro['hora_fin_snapshot']})",
                ),
            )
            self.actualizar_lista_patentes()
            self.reset()
        else:
            self.actualizar_estilo_info("error")
            self.info_label.setText("No se pudo registrar el ingreso con Noches.")
            QMessageBox.critical(self, "Error", "No se pudo registrar el ingreso con Noches.")
            self.enfocar_patente()
        self.actualizar_tabla_activos()

    def registrar_salida(self):
        patente = self.input_patente.text().strip().upper()

        salida = registrar_salida_detallada(patente, self.usuario)
        if salida is not None:
            QMessageBox.information(
                self,
                "Salida registrada",
                construir_mensaje_salida(salida),
            )
            self.actualizar_lista_patentes()
            self.reset()
        else:
            noche = obtener_noche_pendiente_por_patente(patente)
            if noche:
                seleccion, confirmado = QInputDialog.getItem(
                    self,
                    "Revisar Noche pendiente",
                    f"{patente} tiene una Noche prepagada pendiente. Selecciona una acción:",
                    ["Finalizar Noche (retirado)", "Convertir a ingreso normal desde 10:00"],
                    0,
                    False,
                )
                if not confirmado:
                    return
                if seleccion == "Finalizar Noche (retirado)":
                    exito = finalizar_noche_pendiente(noche["id_ingreso"], self.usuario)
                    mensaje = "Noche finalizada sin cobro adicional."
                else:
                    inicio = convertir_noche_a_ingreso_normal(noche["id_ingreso"], self.usuario)
                    exito = inicio is not None
                    mensaje = f"Ingreso normal activo desde {formatear_fecha_hora(inicio)}." if inicio else ""
                if exito:
                    QMessageBox.information(self, "Noche revisada", mensaje)
                    self.actualizar_lista_patentes()
                    self.reset()
                    self.actualizar_tabla_activos()
                    return
            self.actualizar_estilo_info("error")
            self.info_label.setText("No se pudo registrar la salida.")
            QMessageBox.critical(self, "Error", "No se pudo registrar la salida.")
            self.enfocar_patente()

        self.actualizar_tabla_activos()

    def reset(self):
        self.input_patente.clear()
        self.patentes_f3 = []
        self.indice_patente_f3 = -1
        self.busqueda_f3 = ""
        self.patentes_f4 = []
        self.indice_patente_f4 = -1
        self.busqueda_f4 = ""
        self.seleccion_f4 = None
        self.boton_ingreso.setEnabled(False)
        self.boton_ingreso_personalizado.setEnabled(False)
        self.boton_ingreso_noches.setEnabled(False)
        self.boton_salida.setEnabled(False)
        self.boton_espera.setEnabled(False)
        self.actualizar_estilo_info("neutro")
        self.info_label.setText("Escribe una patente y presiona Enter o el botón de búsqueda.")
        self.hora_consulta_label.clear()
        self.enfocar_patente()

    def actualizar_tabla_activos(self):
        datos = obtener_vehiculos_activos()
        solo_lavados = []
        try:
            solo_lavados = obtener_solo_lavados_activos()
        except RuntimeError as exc:
            self.actualizar_estilo_info("warn")
            self.info_label.setText(str(exc))
        filas = datos + [self._fila_solo_lavado(op) for op in solo_lavados]
        hay_subida_activa = self.subida_vigente_ahora()

        self.tabla_activos.setSortingEnabled(False)
        self.tabla_activos.setUpdatesEnabled(False)
        self.tabla_activos.clearContents()
        self.tabla_activos.setRowCount(len(filas) + 1)

        total = 0

        for i, vehiculo in enumerate(filas):
            patente = vehiculo["patente"]
            hora = vehiculo["hora"]
            monto = vehiculo["monto"]
            minutos = vehiculo.get("minutos", 0)

            estado_noche = " [NOCHE PENDIENTE]" if vehiculo.get("noche_pendiente") else ""
            patente_mostrar = f"▲ {patente}{estado_noche}" if hay_subida_activa else f"{patente}{estado_noche}"

            item_patente = QTableWidgetItem(patente_mostrar)
            item_patente.setData(Qt.UserRole, vehiculo.get("id_ingreso"))
            item_patente.setData(Qt.UserRole + 1, vehiculo.get("patente_base", patente))
            item_patente.setData(Qt.UserRole + 2, vehiculo.get("en_lavado", False))
            item_patente.setData(Qt.UserRole + 3, vehiculo.get("tipo_fila", "ingreso"))
            item_patente.setData(Qt.UserRole + 4, vehiculo.get("id_operacion_servicio"))
            item_patente.setFlags(item_patente.flags() ^ Qt.ItemIsEditable)
            item_patente.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.tabla_activos.setItem(i, 0, item_patente)

            item_hora = QTableWidgetItem(str(hora))
            item_hora.setFlags(item_hora.flags() ^ Qt.ItemIsEditable)
            item_hora.setTextAlignment(Qt.AlignCenter)
            self.tabla_activos.setItem(i, 1, item_hora)

            item_minutos = QTableWidgetItem(f"{minutos} min")
            item_minutos.setFlags(item_minutos.flags() ^ Qt.ItemIsEditable)
            item_minutos.setTextAlignment(Qt.AlignCenter)
            self.tabla_activos.setItem(i, 2, item_minutos)

            item_monto = QTableWidgetItem(f"${monto:.0f}")
            item_monto.setFlags(item_monto.flags() ^ Qt.ItemIsEditable)
            item_monto.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla_activos.setItem(i, 3, item_monto)

            total += monto

        fila_total = len(filas)

        item_vacio_0 = QTableWidgetItem("")
        item_vacio_1 = QTableWidgetItem("")
        item_vacio_0.setFlags(item_vacio_0.flags() ^ Qt.ItemIsEditable)
        item_vacio_1.setFlags(item_vacio_1.flags() ^ Qt.ItemIsEditable)

        item_total_label = QTableWidgetItem("TOTAL RECAUDADO:")
        item_total_label.setFlags(item_total_label.flags() ^ Qt.ItemIsEditable)
        item_total_label.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

        item_total_monto = QTableWidgetItem(f"${total:.0f}")
        item_total_monto.setFlags(item_total_monto.flags() ^ Qt.ItemIsEditable)
        item_total_monto.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.tabla_activos.setItem(fila_total, 0, item_vacio_0)
        self.tabla_activos.setItem(fila_total, 1, item_vacio_1)
        self.tabla_activos.setItem(fila_total, 2, item_total_label)
        self.tabla_activos.setItem(fila_total, 3, item_total_monto)

        self.aplicar_estilo_fila_total(fila_total)

        self.grupo_tabla.setVisible(len(filas) > 0)
        self.label_leyenda_tabla.setVisible(len(datos) > 0 and hay_subida_activa)

        resumen_banos = obtener_resumen_banos()
        total_banos = float(resumen_banos["total"])
        resumen_caja = obtener_resumen_caja_actual()

        metricas = calcular_metricas_resumen(total, resumen_caja)
        self.card_estacionados.set_valor(str(len(datos)))
        self.card_total_activos.set_valor(f"${metricas['estimado_activos']:.0f}")
        self.card_total_proyectado.set_valor(f"${metricas['total_proyectado']:.0f}")
        self.card_total_turno.set_valor(f"${metricas['total_turno']:.0f}")
        self.card_neto_caja.set_valor(f"${metricas['neto_caja']:.0f}")
        self.card_banos.set_valor(
            f"{resumen_banos['cantidad']} | ${total_banos:.0f}"
        )

        self.tabla_activos.setUpdatesEnabled(True)
        self.tabla_activos.viewport().update()

    def _fila_solo_lavado(self, operacion):
        return {
            "patente": f"Solo lavado: {operacion['patente']}",
            "patente_base": operacion["patente"],
            "hora": self.formatear_fecha_hora_info(operacion.get("fecha_hora_inicio")),
            "minutos": int(operacion.get("minutos") or 0),
            "monto": float(operacion.get("valor_lavado_snapshot") or 0),
            "en_lavado": True,
            "tipo_fila": "solo_lavado",
            "id_operacion_servicio": operacion["id_operacion_servicio"],
        }

    def actualizar_estado_subida(self):
        subida = obtener_subida_activa()

        if not subida:
            self.label_subida.setObjectName("EstadoSubidaInactiva")
            self.label_subida.setText("Subida temporal: no activa")
            self.label_subida.style().unpolish(self.label_subida)
            self.label_subida.style().polish(self.label_subida)
            self.label_subida.update()
            return

        try:
            ahora = datetime.now()

            def normalizar_hora(valor):
                if hasattr(valor, "hour") and hasattr(valor, "minute"):
                    return valor

                valor_str = str(valor).strip()

                try:
                    return datetime.strptime(valor_str, "%H:%M:%S").time()
                except ValueError:
                    return datetime.strptime(valor_str, "%H:%M").time()

            hora_inicio_time = normalizar_hora(subida["hora_inicio"])
            hora_fin_time = normalizar_hora(subida["hora_fin"])

            hora_inicio = datetime.combine(ahora.date(), hora_inicio_time)
            hora_fin = datetime.combine(ahora.date(), hora_fin_time)

            if hora_fin > hora_inicio:
                activa_ahora = hora_inicio <= ahora <= hora_fin
            else:
                fin_dia_siguiente = hora_fin + timedelta(days=1)
                activa_ahora = (
                    ahora >= hora_inicio or
                    ahora <= datetime.combine(ahora.date(), hora_fin_time)
                )

                if ahora.time() <= hora_fin_time:
                    hora_inicio = hora_inicio - timedelta(days=1)
                    hora_fin = fin_dia_siguiente
                else:
                    hora_fin = fin_dia_siguiente

            monto = subida.get("monto_adicional", 0)
            texto_inicio = hora_inicio_time.strftime("%H:%M")
            texto_fin = hora_fin_time.strftime("%H:%M")

            if activa_ahora:
                self.label_subida.setObjectName("EstadoSubidaActiva")
                self.label_subida.setText(
                    f"Subida temporal activa: +${monto} desde {texto_inicio} hasta {texto_fin}"
                )
            else:
                self.label_subida.setObjectName("EstadoSubidaInactiva")
                self.label_subida.setText(
                    f"Subida configurada, pero no activa ahora: +${monto} ({texto_inicio} - {texto_fin})"
                )

        except Exception as e:
            print(f"[WARN] No se pudo actualizar estado de subida: {e}")
            self.label_subida.setObjectName("EstadoSubidaInactiva")
            self.label_subida.setText("Subida temporal: no activa")

        self.label_subida.style().unpolish(self.label_subida)
        self.label_subida.style().polish(self.label_subida)
        self.label_subida.update()

    def marcar_en_espera(self):
        patente = normalizar_patente(self.input_patente.text())
        confirm = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Deseas marcar la patente {patente} como 'en espera'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            exito = marcar_ingreso_en_espera(patente)
            if exito:
                QMessageBox.information(self, "Éxito", "El ingreso ha sido marcado como 'en espera'.")
                self.reset()
                self.actualizar_tabla_activos()
            else:
                self.actualizar_estilo_info("error")
                self.info_label.setText("No se pudo marcar como 'en espera'. Verifica si el vehículo está dentro.")
                QMessageBox.critical(self, "Error", "No se pudo marcar como 'en espera'. Verifica si está dentro.")
                self.enfocar_patente()

    def mostrar_opciones_bano(self):
        """
        Registra un uso de baño usando el valor configurado en el sistema,
        previa confirmación del usuario.
        """

        try:
            config = obtener_configuracion()
            monto = int(config.get("valor_bano", "300"))
        except Exception:
            QMessageBox.critical(
                self,
                "Error",
                "No se pudo obtener el valor configurado para el uso de baño."
            )
            return

        confirmacion = QMessageBox.question(
            self,
            "Confirmar registro de baño",
            f"¿Deseas registrar un uso de baño por ${monto}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirmacion != QMessageBox.Yes:
            return

        exito = registrar_uso_bano(monto, self.usuario)
        if exito:
            QMessageBox.information(
                self,
                "Éxito",
                f"Uso de baño registrado por ${monto}."
            )
            self.actualizar_tabla_activos()
            self.enfocar_patente()
        else:
            QMessageBox.critical(
                self,
                "Error",
                "No se pudo registrar el uso del baño."
            )

    def obtener_vehiculo_seleccionado(self):
        fila = self.tabla_activos.currentRow()
        if fila < 0:
            return None

        item_patente = self.tabla_activos.item(fila, 0)
        if not item_patente:
            return None

        id_ingreso = item_patente.data(Qt.UserRole)
        if item_patente.data(Qt.UserRole + 3) == "solo_lavado":
            return {
                "tipo_fila": "solo_lavado",
                "id_operacion_servicio": item_patente.data(Qt.UserRole + 4),
                "patente": item_patente.data(Qt.UserRole + 1),
                "en_lavado": True,
            }
        if not id_ingreso:
            return None

        return {
            "id_ingreso": id_ingreso,
            "patente": item_patente.data(Qt.UserRole + 1),
            "en_lavado": bool(item_patente.data(Qt.UserRole + 2)),
            "tipo_fila": "ingreso",
        }

    def alternar_lavado_seleccionado(self):
        vehiculo = self.obtener_vehiculo_seleccionado()
        if not vehiculo:
            QMessageBox.warning(
                self,
                "Selecciona un vehículo",
                "Selecciona un vehículo activo en la tabla para iniciar o finalizar lavado."
            )
            return

        if vehiculo.get("tipo_fila") == "solo_lavado":
            self.mostrar_finalizacion_solo_lavado(vehiculo["id_operacion_servicio"])
            return

        if vehiculo["en_lavado"]:
            resultado = finalizar_lavado(vehiculo["id_ingreso"], self.usuario)
            if resultado:
                QMessageBox.information(
                    self,
                    "Lavado finalizado",
                    "El vehículo volvió a estado estacionado.\n\n"
                    f"Patente: {vehiculo['patente']}\n"
                    f"Valor lavado: ${resultado['valor_lavado']:.0f}"
                )
                self.actualizar_tabla_activos()
                return

            QMessageBox.critical(self, "Error", "No se pudo finalizar el lavado.")
            return

        categorias = obtener_categorias_lavado()
        claves = list(categorias.keys())
        opciones = [
            f"{categorias[clave]['label']} - ${categorias[clave]['valor']:.0f}"
            for clave in claves
        ]

        seleccion, confirmado = QInputDialog.getItem(
            self,
            "Seleccionar lavado",
            f"Selecciona el tipo de lavado para {vehiculo['patente']}:",
            opciones,
            0,
            False,
        )

        if not confirmado or not seleccion:
            return

        categoria = claves[opciones.index(seleccion)]
        resultado = iniciar_lavado(vehiculo["id_ingreso"], categoria, self.usuario)
        if resultado:
            QMessageBox.information(
                self,
                "Lavado iniciado",
                "El cobro de estacionamiento quedó pausado mientras dure el lavado.\n\n"
                f"Patente: {vehiculo['patente']}\n"
                f"Valor lavado: ${resultado['valor_lavado']:.0f}"
            )
            self.actualizar_tabla_activos()
            return

        QMessageBox.critical(self, "Error", "No se pudo iniciar el lavado.")

    def iniciar_solo_lavado_desde_patente(self):
        patente = normalizar_patente(self.input_patente.text())
        es_valida, mensaje = self.validar_patente(patente)
        if not es_valida:
            QMessageBox.warning(self, "Atención", mensaje)
            self.enfocar_patente()
            return

        try:
            tipos = [tipo for tipo in list_wash_vehicle_types() if int(tipo.get("activo", 0))]
        except Exception as exc:
            QMessageBox.critical(self, "Solo lavado no disponible", str(exc))
            return
        if not tipos:
            QMessageBox.warning(self, "Sin tipos activos", SOLO_LAVADO_PRICE_CONFIG_MESSAGE)
            return

        opciones = [f"{tipo['nombre']} - ${float(tipo['valor_lavado']):.0f}" for tipo in tipos]
        seleccion, confirmado = QInputDialog.getItem(
            self,
            "Solo lavado",
            f"Selecciona el tipo de lavado para {patente}:",
            opciones,
            0,
            False,
        )
        if not confirmado or not seleccion:
            return

        tipo = tipos[opciones.index(seleccion)]
        try:
            resultado = iniciar_solo_lavado(patente, tipo["id_tipo_vehiculo_lavado"], self.usuario)
        except RuntimeError as exc:
            QMessageBox.critical(self, "Solo lavado no disponible", str(exc))
            return
        if not resultado:
            QMessageBox.warning(self, "No se pudo iniciar", "La patente puede tener un ingreso activo o el tipo elegido no está disponible.")
            return

        QMessageBox.information(
            self,
            "Solo lavado iniciado",
            "El lavado quedó activo sin crear una estadía.\n\n"
            f"Patente: {resultado['patente']}\n"
            f"Valor lavado: ${resultado['valor_lavado_snapshot']:.0f}"
        )
        self.actualizar_tabla_activos()
        self.enfocar_patente(limpiar=True)

    def finalizar_solo_lavado_desde_operacion(self, id_operacion_servicio, cobrar_ahora=True):
        try:
            if cobrar_ahora:
                resultado = finalizar_solo_lavado_cobrando(id_operacion_servicio, self.usuario)
                titulo = "Solo lavado cobrado"
            else:
                resultado = finalizar_solo_lavado_como_estadia(id_operacion_servicio, self.usuario)
                titulo = "Solo lavado convertido en estadía"
        except RuntimeError as exc:
            QMessageBox.critical(self, "Solo lavado no disponible", str(exc))
            return None

        if not resultado:
            QMessageBox.critical(self, "Error", "No se pudo finalizar el solo lavado.")
            return None

        QMessageBox.information(self, titulo, f"Patente: {resultado['patente']}")
        self.actualizar_tabla_activos()
        return resultado

    def mostrar_finalizacion_solo_lavado(self, id_operacion_servicio):
        seleccion, confirmado = QInputDialog.getItem(
            self,
            "Finalizar solo lavado",
            "Selecciona cómo finalizar el solo lavado:",
            ["Cobrar ahora", "Convertir a estadía"],
            0,
            False,
        )
        if not confirmado or not seleccion:
            return
        self.finalizar_solo_lavado_desde_operacion(
            id_operacion_servicio,
            cobrar_ahora=seleccion == "Cobrar ahora",
        )

    def mostrar_cotizacion(self):
        tipo, confirmado = QInputDialog.getItem(
            self,
            "Cotizaciones",
            "Selecciona qué cotizar:",
            ["Estadía", "Lavado", "Mensualidad"],
            0,
            False,
        )
        if not confirmado or not tipo:
            return

        try:
            if tipo == "Estadía":
                tiempos = self._pedir_horarios_cotizacion_estadia()
                if tiempos is None:
                    return
                hora_ingreso, hora_salida = tiempos
                minutos = calcular_minutos_estadia_por_horarios(hora_ingreso, hora_salida)
                monto = calcular_tarifa(minutos)
                cotizacion = preview_cotizacion({"estadia": {"minutos": minutos, "monto_estadia": monto}})
                detalle = (
                    f"Ingreso: {hora_ingreso}\n"
                    f"Salida: {hora_salida}\n"
                    f"Duración: {minutos} min\n"
                    f"{describir_detalle_tarifa(minutos)}"
                )
            elif tipo == "Lavado":
                try:
                    tipos = resolve_wash_quote_options(list_wash_vehicle_types())
                except Exception as exc:
                    if not _es_tabla_lavado_faltante(exc):
                        raise
                    tipos = wash_quote_options_from_legacy_config()
                if not tipos:
                    QMessageBox.warning(
                        self,
                        "Sin precios de lavado",
                        "No hay precios de lavado configurados para cotizar.",
                    )
                    return
                opciones = [f"{item['nombre']} - ${float(item['valor_lavado']):.0f}" for item in tipos]
                seleccion, ok = QInputDialog.getItem(self, "Cotizar lavado", "Tipo de lavado:", opciones, 0, False)
                if not ok or not seleccion:
                    return
                elegido = tipos[opciones.index(seleccion)]
                cotizacion = preview_cotizacion({
                    "lavado": {
                        "tipo_lavado": elegido["nombre"],
                        "monto_lavado": int(elegido["valor_lavado"]),
                    }
                })
                detalle = f"{elegido['nombre']}"
            else:
                monto, ok = QInputDialog.getInt(
                    self,
                    "Cotizar mensualidad",
                    "Monto mensual negociado:",
                    0,
                    0,
                )
                if not ok:
                    return
                if monto <= 0:
                    QMessageBox.warning(self, "Monto inválido", "Ingresá un monto mensual mayor a cero.")
                    return
                patente = self.input_patente.text().strip().upper() or "MENSUAL"
                cotizacion = preview_cotizacion({
                    "mensualidad": {"vehiculos": [{"patente": patente, "monto_mensual": monto}]}
                })
                detalle = f"Mensual: ${monto:.0f}\nEquivalente diario (30 días): ${round(monto / 30):.0f}"

            total = cotizacion.get("total", cotizacion.get("monto", 0))
            QMessageBox.information(
                self,
                "Cotización",
                f"{detalle}\nTotal estimado: ${float(total):.0f}",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo generar la cotización: {exc}")

    def _pedir_horarios_cotizacion_estadia(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Cotizar estadía")

        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Ingresá la hora de ingreso y salida (HH:MM)."))

        input_ingreso = QLineEdit("13:00")
        input_ingreso.setInputMask("99:99")
        input_ingreso.setPlaceholderText("HH:MM")
        input_salida = QLineEdit("19:00")
        input_salida.setInputMask("99:99")
        input_salida.setPlaceholderText("HH:MM")

        layout.addWidget(QLabel("Hora de ingreso"))
        layout.addWidget(input_ingreso)
        layout.addWidget(QLabel("Hora de salida"))
        layout.addWidget(input_salida)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.Accepted:
            return None
        return input_ingreso.text().strip(), input_salida.text().strip()

    def reingresar_vehiculo(self):
        from controllers.registro_controller import obtener_ingresos_editables, reingresar_vehiculo_cerrado

        patente = normalizar_patente(self.input_patente.text())

        es_valida, mensaje = self.validar_patente(patente)
        if not es_valida:
            QMessageBox.warning(self, "Atención", mensaje)
            return

        ingresos = obtener_ingresos_editables()
        ingreso = next((i for i in ingresos if i["patente"] == patente and i["estado"] == "CERRADO"), None)

        if not ingreso:
            QMessageBox.information(self, "No encontrado", "No hay registros cerrados recientes para reingresar.")
            return

        confirmar = QMessageBox.question(
            self, "Revertir salida",
            (
                f"¿Confirma que NO se cobró dinero a {patente} y desea revertir su salida?\n\n"
                "El vehículo conservará su hora de ingreso original."
            ),
            QMessageBox.Yes | QMessageBox.No
        )

        if confirmar != QMessageBox.Yes:
            return

        exito, mensaje = reingresar_vehiculo_cerrado(
            ingreso["id_ingreso"], self.usuario, True
        )
        if not exito and "ticket de salida ya fue impreso" in mensaje:
            confirmar_ticket = QMessageBox.question(
                self,
                "Ticket de salida impreso",
                "Confirma que reconoce que el ticket de salida fue impreso y entregado?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if confirmar_ticket == QMessageBox.Yes:
                exito, mensaje = reingresar_vehiculo_cerrado(
                    ingreso["id_ingreso"], self.usuario, True,
                    confirma_ticket_impreso=True,
                )

        if exito:
            QMessageBox.information(self, "Salida revertida", mensaje)
            self.actualizar_tabla_activos()
        else:
            QMessageBox.warning(self, "No se pudo revertir", mensaje)

    def consultar_tarifa_actual(self):
        patente = self.input_patente.text().strip().upper()
        if not patente:
            QMessageBox.warning(self, "Error", "Primero escribe una patente.")
            return

        activos = obtener_vehiculos_activos()
        vehiculo = next((v for v in activos if patente in v["patente"]), None)

        if vehiculo:
            monto = vehiculo["monto"]
            QMessageBox.information(self, "Tarifa actual", f"Tarifa acumulada: ${monto}")
        else:
            QMessageBox.information(self, "No encontrado", "El vehículo no está actualmente en el estacionamiento.")

    def alternar_espera_desde_tecla(self):
        patente = self.input_patente.text().strip().upper()

        es_valida, mensaje = self.validar_patente(patente)
        if not es_valida:
            QMessageBox.warning(self, "Atención", mensaje)
            return

        seleccion = self.seleccion_f4
        if isinstance(seleccion, dict) and seleccion.get("estado") == "CERRADO":
            confirmar = QMessageBox.question(
                self,
                "Enviar salida a espera",
                "Confirma que no se cobró dinero y que la salida debe quedar en espera para revisión administrativa?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if confirmar != QMessageBox.Yes:
                return

            exito, mensaje = enviar_salida_sin_cobro_a_espera(
                seleccion["id_ingreso"], self.usuario, True, patente_esperada=seleccion["patente"]
            )
            if not exito and "ticket de salida ya fue impreso" in mensaje:
                confirmar_ticket = QMessageBox.question(
                    self,
                    "Ticket de salida impreso",
                    "Confirma que reconoce que el ticket de salida fue impreso y entregado?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if confirmar_ticket == QMessageBox.Yes:
                    exito, mensaje = enviar_salida_sin_cobro_a_espera(
                        seleccion["id_ingreso"], self.usuario, True,
                        confirma_ticket_impreso=True,
                        patente_esperada=seleccion["patente"],
                    )
        else:
            exito, mensaje = alternar_estado_espera(patente)

        if exito:
            QMessageBox.information(self, "Listo", mensaje)
            self.reset()
            self.actualizar_tabla_activos()
        else:
            QMessageBox.critical(self, "Error", mensaje)

    def eliminar_ingreso_desde_tecla(self):
        if self.rol != "administrador":
            QMessageBox.warning(
                self,
                "Permisos insuficientes",
                "Solo un administrador puede eliminar ingresos."
            )
            return

        patente = self.input_patente.text().strip().upper()
        es_valida, mensaje = self.validar_patente(patente)
        if not es_valida:
            QMessageBox.warning(self, "Atención", mensaje)
            return

        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            (
                f"¿Deseas eliminar el ingreso en espera de la patente {patente}?\n\n"
                "Este movimiento se respaldará en la tabla de ingresos eliminados."
            ),
            QMessageBox.Yes | QMessageBox.No
        )

        if respuesta != QMessageBox.Yes:
            return

        exito, msg = eliminar_ingreso_activo_por_patente(patente, self.usuario)

        if exito:
            QMessageBox.information(self, "Ingreso eliminado", msg)
            self.actualizar_lista_patentes()
            self.reset()
            self.actualizar_tabla_activos()
        else:
            QMessageBox.warning(self, "No se pudo eliminar", msg)

    def abrir_dialogo_subida(self):
        dialogo = SubidaDialog()
        if dialogo.exec():
            hora_inicio, hora_fin, monto = dialogo.obtener_datos()

            exito = crear_subida_temporal(hora_inicio, hora_fin, monto)
            if exito:
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Subida temporal registrada correctamente:\n+${monto} desde {hora_inicio} hasta {hora_fin}"
                )
                self.actualizar_estado_subida()
                self.actualizar_tabla_activos()
                self.enfocar_patente()
            else:
                QMessageBox.warning(self, "Error", "No se pudo registrar la subida.")

    def normalizar_patente_busqueda(self, texto: str):
        texto_normalizado = texto.upper()
        if texto != texto_normalizado:
            cursor_pos = self.input_patente.cursorPosition()
            self.input_patente.blockSignals(True)
            self.input_patente.setText(texto_normalizado)
            self.input_patente.setCursorPosition(min(cursor_pos, len(texto_normalizado)))
            self.input_patente.blockSignals(False)

    def reiniciar_busqueda_f4(self, texto):
        self.busqueda_f4 = texto
        self.patentes_f4 = []
        self.indice_patente_f4 = -1
        self.seleccion_f4 = None

    def reiniciar_busqueda_f3(self, texto):
        self.busqueda_f3 = texto
        self.patentes_f3 = []
        self.indice_patente_f3 = -1

    def validar_patente(self, patente: str) -> tuple[bool, str]:
        if not normalizar_patente(patente):
            return False, "Ingresa una patente."
        if not validar_patente(patente):
            return False, "Patente inválida. Usa ABCD12, ABC12, AB123CD o ABC123."
        return True, ""

    def actualizar_estilo_info(self, tipo: str):
        mapa = {
            "neutro": "EstadoInfoNeutro",
            "ok": "EstadoInfoOk",
            "warn": "EstadoInfoWarn",
            "error": "EstadoInfoError",
        }

        self.info_label.setObjectName(mapa.get(tipo, "EstadoInfoNeutro"))
        self.info_label.style().unpolish(self.info_label)
        self.info_label.style().polish(self.info_label)
        self.info_label.update()

    def enfocar_patente(self, limpiar=False):
        if limpiar:
            self.input_patente.clear()

        self.input_patente.setFocus()
        self.input_patente.selectAll()

    def actualizar_lista_patentes(self):
        try:
            patentes = obtener_patentes_existentes()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudieron cargar las patentes:\n{e}")
            return

        modelo = self.completer_patentes.model()
        if modelo is not None:
            modelo.setStringList(patentes)

    def actualizar_pantalla(self):
        """
        Refresca datos visibles que pueden cambiar desde mobile/API.
        """
        self.patentes_f3 = []
        self.indice_patente_f3 = -1
        self.patentes_f4 = []
        self.indice_patente_f4 = -1
        self.seleccion_f4 = None
        self.actualizar_tabla_activos()
        self.actualizar_lista_patentes()
        self.actualizar_estado_subida()
        self.actualizar_visibilidad_header_tabla()
        self.info_label.setText("Pantalla actualizada con los últimos datos disponibles.")
        self.actualizar_estilo_info("neutro")

    def normalizar_hora_tabla(self, valor):
        if hasattr(valor, "hour") and hasattr(valor, "minute"):
            return valor

        valor_str = str(valor).strip()

        try:
            return datetime.strptime(valor_str, "%H:%M:%S").time()
        except ValueError:
            return datetime.strptime(valor_str, "%H:%M").time()

    def subida_vigente_ahora(self):
        subida = obtener_subida_activa()
        if not subida:
            return False

        try:
            ahora = datetime.now()

            hora_inicio_time = self.normalizar_hora_tabla(subida["hora_inicio"])
            hora_fin_time = self.normalizar_hora_tabla(subida["hora_fin"])

            hora_inicio = datetime.combine(ahora.date(), hora_inicio_time)
            hora_fin = datetime.combine(ahora.date(), hora_fin_time)

            if hora_fin > hora_inicio:
                return hora_inicio <= ahora <= hora_fin

            return ahora >= hora_inicio or ahora.time() <= hora_fin_time

        except Exception as e:
            print(f"[WARN] No se pudo evaluar subida vigente: {e}")
            return False

    def aplicar_estilo_fila_total(self, fila_total):
        for col in range(self.tabla_activos.columnCount()):
            item = self.tabla_activos.item(fila_total, col)
            if item:
                fuente = item.font()
                fuente.setBold(True)
                item.setFont(fuente)
                item.setBackground(self.palette().alternateBase())

    def cargar_patente_desde_tabla(self, fila, columna):
        item_patente = self.tabla_activos.item(fila, 0)
        if not item_patente:
            return

        patente = item_patente.data(Qt.UserRole + 1) or item_patente.text().replace("▲ ", "").strip()
        if item_patente.data(Qt.UserRole + 3) == "solo_lavado":
            self.mostrar_finalizacion_solo_lavado(item_patente.data(Qt.UserRole + 4))
            return
        if not patente:
            return

        self.input_patente.setText(patente)
        self.input_patente.setFocus()
        self.buscar_vehiculo()

    def actualizar_visibilidad_header_tabla(self):
        """
        Oculta el encabezado horizontal de la tabla de vehículos activos
        cuando el usuario se desplaza hacia abajo, y lo vuelve a mostrar
        cuando regresa al inicio.
        """
        scrollbar = self.tabla_activos.verticalScrollBar()
        header = self.tabla_activos.horizontalHeader()

        if scrollbar.value() > 0:
            header.hide()
        else:
            header.show()

    def seleccionar_patente_autocompletada(self, patente):
        """
        Completa automáticamente la patente seleccionada desde el autocompletado
        y ejecuta la búsqueda de inmediato.

        Args:
            patente (str): Patente seleccionada desde el QCompleter.
        """
        if not patente:
            return

        self.input_patente.setText(str(patente).strip().upper())
        self.buscar_vehiculo()

    def accion_f1(self):
        """
        Ejecuta la acción principal disponible para la patente actual:
        registrar ingreso o registrar salida.
        """
        if self.boton_ingreso.isEnabled():
            self.registrar_ingreso()
        elif self.boton_salida.isEnabled():
            self.registrar_salida()
        else:
            QMessageBox.information(
                self,
                "Sin acción",
                "No hay acción disponible para F1."
            )

    def configurar_atajos(self):
        """
        Configura los atajos globales de teclado para la ventana de registro.
        Funcionan mientras la ventana esté activa, sin depender del foco
        exacto en el campo de patente.
        """
        self.shortcut_f1 = QShortcut(QKeySequence("F1"), self)
        self.shortcut_f1.activated.connect(self.accion_f1)

        self.shortcut_f2 = QShortcut(QKeySequence("F2"), self)
        self.shortcut_f2.activated.connect(self.reset)

        self.shortcut_f3 = QShortcut(QKeySequence("F3"), self)
        self.shortcut_f3.activated.connect(self.seleccionar_siguiente_patente_abierta)

        self.shortcut_f4 = QShortcut(QKeySequence("F4"), self)
        self.shortcut_f4.activated.connect(self.seleccionar_siguiente_patente_turno)

        self.shortcut_f6 = QShortcut(QKeySequence("F6"), self)
        self.shortcut_f6.activated.connect(self.mostrar_opciones_bano)

        self.shortcut_f7 = QShortcut(QKeySequence("F7"), self)
        self.shortcut_f7.activated.connect(self.reingresar_vehiculo)

        self.shortcut_f8 = QShortcut(QKeySequence("F8"), self)
        self.shortcut_f8.activated.connect(self.alternar_espera_desde_tecla)

        self.shortcut_f9 = QShortcut(QKeySequence("F9"), self)
        self.shortcut_f9.activated.connect(self.eliminar_ingreso_desde_tecla)

        self.shortcut_f10 = QShortcut(QKeySequence("F10"), self)
        self.shortcut_f10.activated.connect(self.consultar_tarifa_actual)

        self.shortcut_f11 = QShortcut(QKeySequence("F11"), self)
        self.shortcut_f11.activated.connect(self.registrar_ingreso_con_hora_personalizada)

        self.shortcut_lavado = QShortcut(QKeySequence("Ctrl+L"), self)
        self.shortcut_lavado.activated.connect(self.alternar_lavado_seleccionado)

        self.shortcut_escape = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.shortcut_escape.activated.connect(self.reset)
