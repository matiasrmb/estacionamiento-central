from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTableWidget,
    QTableWidgetItem, QGroupBox, QHeaderView, QCompleter,
    QHBoxLayout, QGridLayout, QFrame
)
from PySide6.QtCore import QTimer, Qt
from datetime import datetime, timedelta
from controllers.registro_controller import (
    buscar_estado_vehiculo, registrar_ingreso,
    registrar_salida, obtener_vehiculos_activos,
    marcar_ingreso_en_espera, alternar_estado_espera,
    obtener_patentes_existentes, eliminar_ingreso_activo_por_patente
)
from controllers.subida_controller import crear_subida_temporal, obtener_subida_activa
from views.admin_edicion import EdicionIngresosWindow
from views.subida_dialog import SubidaDialog


class RegistroWindow(QWidget):
    """
    Vista principal para el registro de ingresos y salidas de vehículos.
    """

    def __init__(self, usuario, rol="operador", on_volver_panel=None):
        super().__init__()
        self.usuario = usuario
        self.rol = rol
        self.on_volver_panel = on_volver_panel
        self.setMinimumSize(1000, 650)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # =========================================================
        # ENCABEZADO
        # =========================================================
        header_layout = QHBoxLayout()

        self.boton_volver = QPushButton("Volver al panel principal")
        self.boton_volver.setObjectName("BotonSecundario")
        self.boton_volver.setMinimumHeight(38)
        self.boton_volver.clicked.connect(self.volver_al_panel)

        titulo = QLabel("Registro de vehículos")
        titulo.setObjectName("TituloVentana")
        titulo.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(self.boton_volver, alignment=Qt.AlignLeft)
        header_layout.addStretch()
        header_layout.addWidget(titulo)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # =========================================================
        # BLOQUE SUPERIOR
        # =========================================================
        superior_layout = QGridLayout()
        superior_layout.setHorizontalSpacing(16)
        superior_layout.setVerticalSpacing(16)

        # -------- Búsqueda / patente --------
        grupo_busqueda = QGroupBox("Consulta de patente")
        layout_busqueda = QVBoxLayout()
        layout_busqueda.setContentsMargins(14, 18, 14, 18)
        layout_busqueda.setSpacing(10)

        self.label_patente = QLabel("Patente del vehículo:")
        self.input_patente = QLineEdit()
        self.input_patente.setObjectName("InputPatente")
        self.input_patente.setPlaceholderText("Ej: ABCD12")
        self.input_patente.setMaxLength(8)
        self.input_patente.setMinimumHeight(42)
        self.input_patente.textChanged.connect(self.normalizar_patente)

        patentes = obtener_patentes_existentes()
        self.completer_patentes = QCompleter(patentes, self)
        self.completer_patentes.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer_patentes.setFilterMode(Qt.MatchContains)
        self.input_patente.setCompleter(self.completer_patentes)

        self.boton_buscar = QPushButton("Buscar estado del vehículo")
        self.boton_buscar.setMinimumHeight(40)
        self.boton_buscar.clicked.connect(self.buscar_vehiculo)

        self.boton_refrescar_patentes = QPushButton("Actualizar lista de patentes")
        self.boton_refrescar_patentes.setObjectName("BotonSecundario")
        self.boton_refrescar_patentes.setMinimumHeight(38)
        self.boton_refrescar_patentes.clicked.connect(self.actualizar_lista_patentes)

        self.info_label = QLabel("Escribe una patente y presiona Enter o el botón de búsqueda.")
        self.info_label.setObjectName("EstadoInfoNeutro")
        self.actualizar_estilo_info("neutro")
        self.info_label.setWordWrap(True)

        layout_busqueda.addWidget(self.label_patente)
        layout_busqueda.addWidget(self.input_patente)
        layout_busqueda.addWidget(self.boton_buscar)
        layout_busqueda.addWidget(self.boton_refrescar_patentes)
        layout_busqueda.addWidget(self.info_label)
        layout_busqueda.addStretch()

        grupo_busqueda.setLayout(layout_busqueda)

        # -------- Acciones --------
        grupo_acciones = QGroupBox("Acciones disponibles")
        layout_acciones = QVBoxLayout()
        layout_acciones.setContentsMargins(14, 18, 14, 18)
        layout_acciones.setSpacing(10)

        self.boton_ingreso = QPushButton("Registrar ingreso")
        self.boton_ingreso.setEnabled(False)
        self.boton_ingreso.setMinimumHeight(42)
        self.boton_ingreso.clicked.connect(self.registrar_ingreso)

        self.boton_salida = QPushButton("Registrar salida")
        self.boton_salida.setEnabled(False)
        self.boton_salida.setMinimumHeight(42)
        self.boton_salida.clicked.connect(self.registrar_salida)

        self.boton_espera = QPushButton("Marcar como en espera")
        self.boton_espera.setEnabled(False)
        self.boton_espera.setMinimumHeight(42)
        self.boton_espera.clicked.connect(self.marcar_en_espera)

        self.boton_bano = QPushButton("Registrar uso de baño")
        self.boton_bano.setMinimumHeight(42)
        self.boton_bano.clicked.connect(self.mostrar_opciones_bano)

        layout_acciones.addWidget(self.boton_ingreso)
        layout_acciones.addWidget(self.boton_salida)
        layout_acciones.addWidget(self.boton_espera)
        layout_acciones.addWidget(self.boton_bano)

        if self.rol == "administrador":
            self.btn_edicion = QPushButton("Edición manual de ingresos")
            self.btn_edicion.setMinimumHeight(42)
            self.btn_edicion.clicked.connect(self.abrir_edicion)

            self.boton_subida = QPushButton("Subida temporal de precios")
            self.boton_subida.setMinimumHeight(42)
            self.boton_subida.clicked.connect(self.abrir_dialogo_subida)

            layout_acciones.addWidget(self.btn_edicion)
            layout_acciones.addWidget(self.boton_subida)

        layout_acciones.addStretch()
        grupo_acciones.setLayout(layout_acciones)

        # -------- Panel lateral informativo --------
        grupo_estado = QGroupBox("Estado actual")
        layout_estado = QVBoxLayout()
        layout_estado.setContentsMargins(14, 18, 14, 18)
        layout_estado.setSpacing(10)

        self.label_usuario_activo = QLabel(f"Usuario: {self.usuario} ({self.rol})")
        self.label_usuario_activo.setWordWrap(True)

        self.label_subida = QLabel("Subida temporal: no activa")
        self.label_subida.setWordWrap(True)

        self.label_atajos = QLabel(
            "Atajos rápidos:\n"
            "F1: ingresar / salir\n"
            "F2: limpiar formulario\n"
            "F3: enfocar patente\n"
            "Enter: buscar patente\n"
            "Esc: limpiar y volver al inicio\n"
            "F6: registrar baño\n"
            "F7: reingresar vehículo\n"
            "F8: alternar espera\n"
            "F9: eliminar ingreso\n"
            "F10: consultar tarifa"
        )
        self.label_atajos.setWordWrap(True)

        layout_estado.addWidget(self.label_usuario_activo)
        layout_estado.addWidget(self.label_subida)
        layout_estado.addWidget(self.label_atajos)
        layout_estado.addStretch()

        grupo_estado.setLayout(layout_estado)

        superior_layout.addWidget(grupo_busqueda, 0, 0)
        superior_layout.addWidget(grupo_acciones, 0, 1)
        superior_layout.addWidget(grupo_estado, 0, 2)

        superior_layout.setColumnStretch(0, 2)
        superior_layout.setColumnStretch(1, 2)
        superior_layout.setColumnStretch(2, 1)

        layout.addLayout(superior_layout)

        # =========================================================
        # RESUMEN + TABLA
        # =========================================================
        resumen_layout = QHBoxLayout()
        resumen_layout.setSpacing(14)

        self.card_estacionados = self.crear_tarjeta_resumen("Vehículos activos", "0")
        self.card_total = self.crear_tarjeta_resumen("Total acumulado", "$0")

        resumen_layout.addWidget(self.card_estacionados)
        resumen_layout.addWidget(self.card_total)
        resumen_layout.addStretch()

        layout.addLayout(resumen_layout)

        self.grupo_tabla = QGroupBox("Vehículos actualmente estacionados")
        self.grupo_tabla.setVisible(False)

        layout_tabla = QVBoxLayout()
        layout_tabla.setContentsMargins(10, 20, 10, 20)

        self.tabla_activos = QTableWidget()
        self.tabla_activos.setObjectName("TablaActivos")
        self.tabla_activos.setColumnCount(4)
        self.tabla_activos.setHorizontalHeaderLabels(["Patente", "Hora ingreso", "Minutos", "Monto actual"])
        self.tabla_activos.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tabla_activos.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_activos.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla_activos.verticalHeader().setDefaultSectionSize(34)

        self.tabla_activos.horizontalHeader().setStretchLastSection(True)
        self.tabla_activos.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla_activos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla_activos.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabla_activos.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

        self.tabla_activos.cellDoubleClicked.connect(self.cargar_patente_desde_tabla)

        layout_tabla.addWidget(self.tabla_activos)
        self.label_leyenda_tabla = QLabel("▲ indica que existe una subida temporal vigente para los vehículos mostrados.")
        self.label_leyenda_tabla.setObjectName("LeyendaTabla")
        layout_tabla.addWidget(self.label_leyenda_tabla)
        self.grupo_tabla.setLayout(layout_tabla)
        layout.addWidget(self.grupo_tabla)

        self.timer_tabla = QTimer()
        self.timer_tabla.timeout.connect(self.actualizar_tabla_activos)
        self.timer_tabla.timeout.connect(self.actualizar_estado_subida) 
        self.timer_tabla.start(5000)

        self.actualizar_tabla_activos()
        self.actualizar_lista_patentes()
        self.actualizar_estado_subida()

        self.input_patente.setFocus()

        self.setLayout(layout)

        QTimer.singleShot(0, self.input_patente.setFocus)

    def crear_tarjeta_resumen(self, titulo, valor):
        frame = QFrame()
        frame.setObjectName("TarjetaResumen")
        frame.setMinimumHeight(90)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)

        label_titulo = QLabel(titulo)
        label_titulo.setStyleSheet("font-size: 13px; color: #6b7280;")

        label_valor = QLabel(valor)
        label_valor.setStyleSheet("font-size: 22px; font-weight: 700; color: #111827;")

        layout.addWidget(label_titulo)
        layout.addWidget(label_valor)

        frame.label_titulo = label_titulo
        frame.label_valor = label_valor
        return frame

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

            if hay_subida_activa:
                for item in (item_patente, item_hora, item_minutos, item_monto):
                    item.setBackground(Qt.yellow)

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

        self.card_estacionados.label_valor.setText(str(len(datos)))
        self.card_total.label_valor.setText(f"${total:.0f}")

        self.tabla_activos.setUpdatesEnabled(True)
        self.tabla_activos.viewport().update()

    def actualizar_estado_subida(self):
        """
        Actualiza el label de subida temporal mostrando si la subida activa
        en base de datos está vigente en este momento o solo configurada.
        """
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
                """
                Convierte distintos formatos de hora a objeto time.
                Soporta:
                - datetime.time
                - str 'HH:MM'
                - str 'HH:MM:SS'
                """
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

            # Caso normal: mismo día
            if hora_fin > hora_inicio:
                activa_ahora = hora_inicio <= ahora <= hora_fin

            # Caso cruza medianoche
            else:
                fin_dia_siguiente = hora_fin + timedelta(days=1)

                # tramo nocturno: desde hora_inicio hasta medianoche, o desde 00:00 hasta hora_fin
                activa_ahora = (
                    ahora >= hora_inicio or
                    ahora <= datetime.combine(ahora.date(), hora_fin_time)
                )

                # si estamos después de medianoche y antes de hora_fin,
                # reconstruimos rango lógico solo para mostrar mejor
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

    def abrir_edicion(self):
        self.ventana_edicion = EdicionIngresosWindow(self.usuario)
        self.ventana_edicion.show()

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
        from PySide6.QtWidgets import QInputDialog
        from controllers.registro_controller import registrar_uso_bano

        opciones = ["$300", "$400", "$500"]
        monto_str, ok = QInputDialog.getItem(
            self, "Registrar Baño", "Seleccione el monto:", opciones, 0, False
        )
        if ok and monto_str:
            monto = int(monto_str.replace("$", ""))
            exito = registrar_uso_bano(monto, self.usuario)
            if exito:
                QMessageBox.information(self, "Éxito", f"Uso de baño registrado por ${monto}")
                self.enfocar_patente()
            else:
                QMessageBox.critical(self, "Error", "No se pudo registrar el uso del baño.")

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
            QMessageBox.information(self, "Tarifa Actual", f"Tarifa acumulada: ${monto}")
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
                f"¿Deseas eliminar el ingreso ACTIVO de la patente {patente}?\n\n"
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
        """
        Cambia el estilo visual del label informativo según el estado.
        """
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
        """
        Devuelve el foco al campo patente. Opcionalmente limpia el contenido.
        """
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
        """
        Convierte distintos formatos de hora a objeto time.
        """
        if hasattr(valor, "hour") and hasattr(valor, "minute"):
            return valor

        valor_str = str(valor).strip()

        try:
            return datetime.strptime(valor_str, "%H:%M:%S").time()
        except ValueError:
            return datetime.strptime(valor_str, "%H:%M").time()

    def subida_vigente_ahora(self):
        """
        Retorna True si la subida temporal activa en BD está vigente en este momento.
        """
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
        """
        Aplica estilo visual a la fila de total recaudado.
        """
        for col in range(self.tabla_activos.columnCount()):
            item = self.tabla_activos.item(fila_total, col)
            if item:
                fuente = item.font()
                fuente.setBold(True)
                item.setFont(fuente)
                item.setBackground(self.palette().alternateBase())

    def cargar_patente_desde_tabla(self, fila, columna):
        """
        Carga la patente de una fila seleccionada al campo de búsqueda.
        Ignora la fila de total.
        """
        item_patente = self.tabla_activos.item(fila, 0)
        if not item_patente:
            return

        patente = item_patente.text().replace("▲ ", "").strip()
        if not patente:
            return

        self.input_patente.setText(patente)
        self.input_patente.setFocus()
        self.buscar_vehiculo()

    def keyPressEvent(self, event):
        tecla = event.key()

        if tecla == Qt.Key_F1:
            if self.boton_ingreso.isEnabled():
                self.registrar_ingreso()
            elif self.boton_salida.isEnabled():
                self.registrar_salida()
            else:
                QMessageBox.information(self, "Sin acción", "No hay acción disponible para F1.")

        elif tecla == Qt.Key_F2:
            self.reset()

        elif tecla == Qt.Key_F3:
            self.enfocar_patente()

        elif tecla == Qt.Key_F6:
            self.mostrar_opciones_bano()

        elif tecla == Qt.Key_F7:
            self.reingresar_vehiculo()

        elif tecla == Qt.Key_F8:
            self.alternar_espera_desde_tecla()

        elif tecla == Qt.Key_F9:
            self.eliminar_ingreso_desde_tecla()

        elif tecla == Qt.Key_F10:
            self.consultar_tarifa_actual()

        elif tecla == Qt.Key_Escape:
            self.reset()

        elif tecla == Qt.Key_Return or tecla == Qt.Key_Enter:
            self.buscar_vehiculo()

        else:
            super().keyPressEvent(event)