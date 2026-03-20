from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTableWidget,
    QTableWidgetItem, QGroupBox, QHeaderView, QCompleter,
    QHBoxLayout
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
    Permite buscar vehículos por patente, registrar ingresos y salidas,
    ver vehículos activos y volver al panel principal.
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
        layout.setSpacing(15)

        # Encabezado con volver
        header_layout = QHBoxLayout()

        self.boton_volver = QPushButton("⬅ Volver al panel principal")
        self.boton_volver.setObjectName("BotonSecundario")
        self.boton_volver.clicked.connect(self.volver_al_panel)

        titulo = QLabel("Registro de vehículos")
        titulo.setObjectName("TituloVentana")
        titulo.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(self.boton_volver, alignment=Qt.AlignLeft)
        header_layout.addStretch()
        header_layout.addWidget(titulo)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        grupo_registro = QGroupBox("🔎 Registro de Vehículo")
        layout_registro = QVBoxLayout()
        layout_registro.setContentsMargins(10, 20, 10, 20)

        self.label_patente = QLabel("Patente del vehículo:")
        self.input_patente = QLineEdit()
        self.input_patente.setObjectName("InputPatente")
        self.input_patente.setPlaceholderText("Ej: ABCD12")
        self.input_patente.setMaxLength(8)
        self.input_patente.textChanged.connect(self.normalizar_patente)

        patentes = obtener_patentes_existentes()
        self.completer_patentes = QCompleter(patentes, self)
        self.completer_patentes.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer_patentes.setFilterMode(Qt.MatchContains)
        self.input_patente.setCompleter(self.completer_patentes)

        self.boton_buscar = QPushButton("🔍 Buscar")
        self.boton_buscar.clicked.connect(self.buscar_vehiculo)

        self.boton_refrescar_patentes = QPushButton("🔄 Actualizar lista de patentes")
        self.boton_refrescar_patentes.setObjectName("BotonSecundario")
        self.boton_refrescar_patentes.clicked.connect(self.actualizar_lista_patentes)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: gray; font-size: 13px; padding: 5px 0;")

        self.boton_ingreso = QPushButton("🚗 Registrar Ingreso")
        self.boton_ingreso.setEnabled(False)
        self.boton_ingreso.clicked.connect(self.registrar_ingreso)

        self.boton_salida = QPushButton("🏁 Registrar Salida")
        self.boton_salida.setEnabled(False)
        self.boton_salida.clicked.connect(self.registrar_salida)

        self.boton_bano = QPushButton("🚻 Registrar Uso de Baño")
        self.boton_bano.clicked.connect(self.mostrar_opciones_bano)

        self.boton_espera = QPushButton("⏸️ Marcar como en espera")
        self.boton_espera.setEnabled(False)
        self.boton_espera.clicked.connect(self.marcar_en_espera)

        layout_registro.addWidget(self.label_patente)
        layout_registro.addWidget(self.input_patente)
        layout_registro.addWidget(self.boton_buscar)
        layout_registro.addWidget(self.boton_refrescar_patentes)
        layout_registro.addWidget(self.info_label)
        layout_registro.addWidget(self.boton_ingreso)
        layout_registro.addWidget(self.boton_salida)
        layout_registro.addWidget(self.boton_espera)
        layout_registro.addWidget(self.boton_bano)

        if self.rol == "administrador":
            self.btn_edicion = QPushButton("✏️ Edición de ingresos")
            self.btn_edicion.clicked.connect(self.abrir_edicion)

            self.boton_subida = QPushButton("📈 Subida de precios")
            self.boton_subida.clicked.connect(self.abrir_dialogo_subida)

            layout_registro.addWidget(self.btn_edicion)
            layout_registro.addWidget(self.boton_subida)

        grupo_registro.setLayout(layout_registro)
        layout.addWidget(grupo_registro)

        self.grupo_tabla = QGroupBox("🚗 Vehículos actualmente estacionados")
        self.grupo_tabla.setVisible(False)

        layout_tabla = QVBoxLayout()
        layout_tabla.setContentsMargins(10, 20, 10, 20)

        self.tabla_activos = QTableWidget()
        self.tabla_activos.setColumnCount(4)
        self.tabla_activos.setHorizontalHeaderLabels(["Patente", "Hora Ingreso", "Minutos", "Monto Actual"])
        self.tabla_activos.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.tabla_activos.horizontalHeader().setStretchLastSection(True)
        self.tabla_activos.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla_activos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla_activos.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabla_activos.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tabla_activos.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_activos.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla_activos.verticalHeader().setDefaultSectionSize(34)
        layout_tabla.addWidget(self.tabla_activos)
        self.grupo_tabla.setLayout(layout_tabla)
        layout.addWidget(self.grupo_tabla)

        self.timer_tabla = QTimer()
        self.timer_tabla.timeout.connect(self.actualizar_tabla_activos)
        self.timer_tabla.start(5000)

        self.actualizar_tabla_activos()
        self.actualizar_lista_patentes()

        self.setLayout(layout)

    def volver_al_panel(self):
        if callable(self.on_volver_panel):
            self.on_volver_panel()

    def buscar_vehiculo(self):
        patente = self.input_patente.text().strip().upper()

        es_valida, mensaje = self.validar_patente(patente)
        if not es_valida:
            QMessageBox.warning(self, "Atención", mensaje)
            return

        estado = buscar_estado_vehiculo(patente)
        self.info_label.setText("")

        if estado == "no_registrado":
            self.info_label.setText("Vehículo no registrado. Se creará al ingresar.")
            self.boton_ingreso.setEnabled(True)
            self.boton_salida.setEnabled(False)
            self.boton_espera.setEnabled(False)

        elif estado == "dentro":
            self.info_label.setText("Vehículo actualmente en el estacionamiento.")
            self.boton_salida.setEnabled(True)
            self.boton_ingreso.setEnabled(False)
            self.boton_espera.setEnabled(True)

        elif estado == "fuera":
            self.info_label.setText("Vehículo ya salió. Puedes registrar nuevo ingreso.")
            self.boton_ingreso.setEnabled(True)
            self.boton_salida.setEnabled(False)
            self.boton_espera.setEnabled(False)

        else:
            self.info_label.setText("Estado desconocido.")
            self.boton_ingreso.setEnabled(False)
            self.boton_salida.setEnabled(False)
            self.boton_espera.setEnabled(False)
            QMessageBox.critical(self, "Error", "Error al consultar la patente.")

    def registrar_ingreso(self):
        patente = self.input_patente.text().strip().upper()

        es_valida, mensaje = self.validar_patente(patente)
        if not es_valida:
            QMessageBox.warning(self, "Atención", mensaje)
            return

        exito = registrar_ingreso(patente)
        if exito:
            QMessageBox.information(self, "Éxito", f"Ingreso registrado para {patente}")
            self.actualizar_lista_patentes()
            self.reset()
        else:
            QMessageBox.critical(self, "Error", "No se pudo registrar el ingreso.")
        self.actualizar_tabla_activos()

    def registrar_salida(self):
        patente = self.input_patente.text().strip().upper()

        es_valida, mensaje = self.validar_patente(patente)
        if not es_valida:
            QMessageBox.warning(self, "Atención", mensaje)
            return

        tarifa = registrar_salida(patente, self.usuario)
        if tarifa is not None:
            QMessageBox.information(self, "Salida registrada", f"Tarifa: ${tarifa:.0f}")
            self.actualizar_lista_patentes()
            self.reset()
        else:
            QMessageBox.critical(self, "Error", "No se pudo registrar la salida.")
        self.actualizar_tabla_activos()

    def reset(self):
        self.input_patente.clear()
        self.boton_ingreso.setEnabled(False)
        self.boton_salida.setEnabled(False)
        self.boton_espera.setEnabled(False)
        self.info_label.setText("")

    def actualizar_tabla_activos(self):
        datos = obtener_vehiculos_activos()

        subida = obtener_subida_activa()
        hay_subida_activa = False
        if subida:
            try:
                hora_actual = datetime.now()
                h_inicio = datetime.combine(
                    hora_actual.date(),
                    datetime.strptime(str(subida["hora_inicio"]), "%H:%M:%S").time()
                )
                h_fin = datetime.combine(
                    hora_actual.date(),
                    datetime.strptime(str(subida["hora_fin"]), "%H:%M:%S").time()
                )

                if h_fin <= h_inicio:
                    h_fin += timedelta(days=1)

                if h_inicio <= hora_actual <= h_fin:
                    hay_subida_activa = True
            except Exception as e:
                print(f"[WARN] No se pudo verificar el rango de la subida: {e}")

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
            self.tabla_activos.setItem(i, 0, item_patente)

            item_hora = QTableWidgetItem(hora)
            item_hora.setFlags(item_hora.flags() ^ Qt.ItemIsEditable)
            self.tabla_activos.setItem(i, 1, item_hora)

            item_minutos = QTableWidgetItem(f"{minutos} min")
            item_minutos.setFlags(item_minutos.flags() ^ Qt.ItemIsEditable)
            item_minutos.setTextAlignment(Qt.AlignCenter)
            self.tabla_activos.setItem(i, 2, item_minutos)

            item_monto = QTableWidgetItem(f"${monto:.0f}")
            item_monto.setFlags(item_monto.flags() ^ Qt.ItemIsEditable)
            self.tabla_activos.setItem(i, 3, item_monto)

            total += monto

        fila_total = len(datos)

        item_total_label = QTableWidgetItem("TOTAL RECAUDADO:")
        item_total_label.setFlags(item_total_label.flags() ^ Qt.ItemIsEditable)
        item_total_label.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.tabla_activos.setItem(fila_total, 2, item_total_label)

        item_total_monto = QTableWidgetItem(f"${total:.0f}")
        item_total_monto.setFlags(item_total_monto.flags() ^ Qt.ItemIsEditable)
        item_total_monto.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.tabla_activos.setItem(fila_total, 3, item_total_monto)

        self.tabla_activos.setItem(fila_total, 0, QTableWidgetItem(""))
        self.tabla_activos.setItem(fila_total, 1, QTableWidgetItem(""))

        self.grupo_tabla.setVisible(len(datos) > 0)

        self.tabla_activos.setUpdatesEnabled(True)
        self.tabla_activos.viewport().update()

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
                QMessageBox.critical(self, "Error", "No se pudo marcar como 'en espera'. Verifica si está dentro.")

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

    def actualizar_lista_patentes(self):
        try:
            patentes = obtener_patentes_existentes()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudieron cargar las patentes:\n{e}")
            return

        modelo = self.completer_patentes.model()
        if modelo is not None:
            modelo.setStringList(patentes)

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
        elif tecla == Qt.Key_Return or tecla == Qt.Key_Enter:
            self.buscar_vehiculo()