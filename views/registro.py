from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTableWidget,
    QTableWidgetItem, QGroupBox, QHeaderView, QCompleter,
    QHBoxLayout, QGridLayout, QFrame, QSizePolicy, QScrollArea
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QShortcut, QKeySequence
from datetime import datetime, timedelta
from controllers.registro_controller import (
    buscar_estado_vehiculo, registrar_ingreso,
    registrar_salida, obtener_vehiculos_activos,
    marcar_ingreso_en_espera, alternar_estado_espera,
    obtener_patentes_existentes, eliminar_ingreso_activo_por_patente,
    registrar_uso_bano
)
from controllers.subida_controller import crear_subida_temporal, obtener_subida_activa
from controllers.config_controller import obtener_configuracion
from controllers.dashboard_controller import obtener_resumen_banos
from views.subida_dialog import SubidaDialog


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

        header_layout.addWidget(self.boton_volver, 0, alignment=Qt.AlignLeft)
        header_layout.addStretch(1)

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
        self.input_patente.setMaxLength(8)
        self.input_patente.setMinimumHeight(42)
        self.input_patente.textChanged.connect(self.normalizar_patente)
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

        layout_busqueda.addWidget(self.label_patente)
        layout_busqueda.addWidget(self.input_patente)
        layout_busqueda.addWidget(self.boton_buscar)
        layout_busqueda.addWidget(self.boton_refrescar_patentes)
        layout_busqueda.addWidget(self.info_label)
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

        layout_acciones.addWidget(self.boton_ingreso)
        layout_acciones.addWidget(self.boton_salida)
        layout_acciones.addWidget(self.boton_espera)
        layout_acciones.addWidget(self.boton_bano)

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
            "F3: enfocar patente\n"
            "F6: registrar baño\n"
            "F7: reingresar vehículo\n"
            "F8: alternar espera\n"
            "F9: eliminar ingreso\n"
            "F10: consultar tarifa"
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

        self.card_estacionados = self.crear_tarjeta_resumen("Vehículos activos", "0")
        self.card_banos = self.crear_tarjeta_resumen("Usos de baño hoy", "0")
        self.card_total = self.crear_tarjeta_resumen("Total general", "$0")

        resumen_layout.addWidget(self.card_estacionados)
        resumen_layout.addWidget(self.card_banos)
        resumen_layout.addWidget(self.card_total)
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

    def crear_tarjeta_resumen(self, titulo, valor):
        frame = QFrame()
        frame.setObjectName("ResumenModulo")
        frame.setMinimumHeight(86)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("TituloResumenModulo")
        label_titulo.setWordWrap(True)

        label_valor = QLabel(valor)
        label_valor.setObjectName("ValorResumenModulo")
        label_valor.setWordWrap(True)

        layout.addWidget(label_titulo)
        layout.addWidget(label_valor)

        frame.label_titulo = label_titulo
        frame.label_valor = label_valor
        return frame

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

        es_valida, mensaje = self.validar_patente(patente)
        if not es_valida:
            self.actualizar_estilo_info("warn")
            self.info_label.setText(mensaje)
            QMessageBox.warning(self, "Atención", mensaje)
            self.enfocar_patente()
            return

        estado = buscar_estado_vehiculo(patente)

        if estado == "no_registrado":
            self.actualizar_estilo_info("ok")
            self.info_label.setText("Vehículo no registrado. Puedes crear su ingreso.")
            self.boton_ingreso.setEnabled(True)
            self.boton_salida.setEnabled(False)
            self.boton_espera.setEnabled(False)

        elif estado == "dentro":
            self.actualizar_estilo_info("warn")
            self.info_label.setText("Vehículo actualmente dentro del estacionamiento. Puedes registrar salida o marcar en espera.")
            self.boton_salida.setEnabled(True)
            self.boton_ingreso.setEnabled(False)
            self.boton_espera.setEnabled(True)

        elif estado == "fuera":
            self.actualizar_estilo_info("neutro")
            self.info_label.setText("Vehículo fuera del estacionamiento. Puedes registrar un nuevo ingreso.")
            self.boton_ingreso.setEnabled(True)
            self.boton_salida.setEnabled(False)
            self.boton_espera.setEnabled(False)

        else:
            self.actualizar_estilo_info("error")
            self.info_label.setText("No fue posible determinar el estado del vehículo.")
            self.boton_ingreso.setEnabled(False)
            self.boton_salida.setEnabled(False)
            self.boton_espera.setEnabled(False)
            QMessageBox.critical(self, "Error", "Error al consultar la patente.")
            self.enfocar_patente()

    def registrar_ingreso(self):
        patente = self.input_patente.text().strip().upper()

        es_valida, mensaje = self.validar_patente(patente)
        if not es_valida:
            self.actualizar_estilo_info("warn")
            self.info_label.setText(mensaje)
            QMessageBox.warning(self, "Atención", mensaje)
            self.enfocar_patente()
            return

        exito = registrar_ingreso(patente)
        if exito:
            QMessageBox.information(self, "Éxito", f"Ingreso registrado para {patente}")
            self.actualizar_lista_patentes()
            self.reset()
        else:
            self.actualizar_estilo_info("error")
            self.info_label.setText("No se pudo registrar el ingreso.")
            QMessageBox.critical(self, "Error", "No se pudo registrar el ingreso.")
            self.enfocar_patente()

        self.actualizar_tabla_activos()

    def registrar_salida(self):
        patente = self.input_patente.text().strip().upper()

        es_valida, mensaje = self.validar_patente(patente)
        if not es_valida:
            self.actualizar_estilo_info("warn")
            self.info_label.setText(mensaje)
            QMessageBox.warning(self, "Atención", mensaje)
            self.enfocar_patente()
            return

        tarifa = registrar_salida(patente, self.usuario)
        if tarifa is not None:
            QMessageBox.information(self, "Salida registrada", f"Tarifa: ${tarifa:.0f}")
            self.actualizar_lista_patentes()
            self.reset()
        else:
            self.actualizar_estilo_info("error")
            self.info_label.setText("No se pudo registrar la salida.")
            QMessageBox.critical(self, "Error", "No se pudo registrar la salida.")
            self.enfocar_patente()

        self.actualizar_tabla_activos()

    def reset(self):
        self.input_patente.clear()
        self.boton_ingreso.setEnabled(False)
        self.boton_salida.setEnabled(False)
        self.boton_espera.setEnabled(False)
        self.actualizar_estilo_info("neutro")
        self.info_label.setText("Escribe una patente y presiona Enter o el botón de búsqueda.")
        self.enfocar_patente()

    def actualizar_tabla_activos(self):
        datos = obtener_vehiculos_activos()
        hay_subida_activa = self.subida_vigente_ahora()

        self.tabla_activos.setSortingEnabled(False)
        self.tabla_activos.setUpdatesEnabled(False)
        self.tabla_activos.clearContents()
        self.tabla_activos.setRowCount(len(datos) + 1)

        total = 0

        for i, vehiculo in enumerate(datos):
            patente = vehiculo["patente"]
            hora = vehiculo["hora"]
            monto = vehiculo["monto"]
            minutos = vehiculo.get("minutos", 0)

            patente_mostrar = f"▲ {patente}" if hay_subida_activa else patente

            item_patente = QTableWidgetItem(patente_mostrar)
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

        fila_total = len(datos)

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

        self.grupo_tabla.setVisible(len(datos) > 0)
        self.label_leyenda_tabla.setVisible(len(datos) > 0 and hay_subida_activa)

        resumen_banos = obtener_resumen_banos()
        total_banos = float(resumen_banos["total"])
        total_general = total + total_banos

        self.card_estacionados.label_valor.setText(str(len(datos)))
        self.card_total.label_valor.setText(f"${total_general:.0f}")
        self.card_banos.label_valor.setText(
            f"{resumen_banos['cantidad']} | ${total_banos:.0f}"
        )

        self.tabla_activos.setUpdatesEnabled(True)
        self.tabla_activos.viewport().update()

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
        patente = self.input_patente.text().strip().upper()
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

    def reingresar_vehiculo(self):
        from controllers.registro_controller import obtener_ingresos_editables, reingresar_vehiculo_cerrado

        patente = self.input_patente.text().strip().upper()

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
            self, "Confirmar reingreso",
            f"¿Deseas reingresar a {patente} manteniendo su hora original?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirmar == QMessageBox.Yes:
            exito = reingresar_vehiculo_cerrado(ingreso["id_ingreso"])
            if exito:
                QMessageBox.information(self, "Reingresado", "Vehículo reingresado con éxito.")
                self.actualizar_tabla_activos()
            else:
                QMessageBox.critical(self, "Error", "No se pudo reingresar el vehículo.")

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
                f"¿Deseas eliminar el ingreso activo de la patente {patente}?\n\n"
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

    def normalizar_patente(self, texto: str):
        texto_mayus = texto.upper()
        if texto != texto_mayus:
            cursor_pos = self.input_patente.cursorPosition()
            self.input_patente.blockSignals(True)
            self.input_patente.setText(texto_mayus)
            self.input_patente.setCursorPosition(cursor_pos)
            self.input_patente.blockSignals(False)

    def validar_patente(self, patente: str) -> tuple[bool, str]:
        if not patente:
            return False, "Ingresa una patente."

        if len(patente) < 4 or len(patente) > 8:
            return False, "La patente debe tener entre 4 y 8 caracteres."

        if not patente.isalnum():
            return False, "La patente solo puede contener letras y números."

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

        patente = item_patente.text().replace("▲ ", "").strip()
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
        self.shortcut_f3.activated.connect(self.enfocar_patente)

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

        self.shortcut_escape = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.shortcut_escape.activated.connect(self.reset)