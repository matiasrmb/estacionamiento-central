from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QTableWidget, 
    QTableWidgetItem, QGroupBox, QHeaderView
)
from PySide6.QtCore import QTimer, Qt
from datetime import datetime
from controllers.registro_controller import (
    buscar_estado_vehiculo, registrar_ingreso, 
    registrar_salida, obtener_vehiculos_activos,
    marcar_ingreso_en_espera
)
from views.dashboard import DashboardWindow
from views.admin_edicion import EdicionIngresosWindow
from functools import partial

class RegistroWindow(QWidget):
    """
    Ventana principal para el registro de ingresos y salidas de vehículos.
    Permite buscar vehículos por patente, registrar ingresos y salidas,
    y ver un resumen diario del estacionamiento.
    """
    def __init__(self, usuario, rol="operador"):
        super().__init__()
        self.usuario = usuario
        self.rol = rol
        self.setWindowTitle("Registro de Vehículos")
        self.setFixedSize(900, 700) 
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Grupo de Registro
        grupo_registro = QGroupBox("🔎 Registro de Vehículo")
        layout_registro = QVBoxLayout()
        layout_registro.setContentsMargins(10, 20, 10, 20)

        self.label_patente = QLabel("Patente del vehículo:")
        self.input_patente = QLineEdit()
        self.input_patente.setPlaceholderText("Ej: ABCD12")
        self.input_patente.setStyleSheet("padding: 6px; font-size: 14px;")

        self.boton_buscar = QPushButton("🔍 Buscar")
        self.boton_buscar.clicked.connect(self.buscar_vehiculo)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: gray; font-size: 13px; padding: 5px 0;")

        self.boton_ingreso = QPushButton("🚗 Registrar Ingreso")
        self.boton_ingreso.setEnabled(False)
        self.boton_ingreso.clicked.connect(self.registrar_ingreso)

        self.boton_salida = QPushButton("🏁 Registrar Salida")
        self.boton_salida.setEnabled(False)
        self.boton_salida.setStyleSheet("""
            QPushButton {
                padding: 6px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
                border: 1px solid #aaaaaa;
            }
        """)
        self.boton_salida.clicked.connect(self.registrar_salida)

        self.boton_bano = QPushButton("🚻 Registrar Uso de Baño")
        self.boton_bano.clicked.connect(self.mostrar_opciones_bano)

        self.boton_espera = QPushButton("⏸️ Marcar como en espera")
        self.boton_espera.setEnabled(False)
        self.boton_espera.setStyleSheet("""
            QPushButton {
                padding: 6px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
                border: 1px solid #aaaaaa;
            }
        """)
        self.boton_espera.clicked.connect(self.marcar_en_espera)

        if self.rol == "administrador":
            self.btn_edicion = QPushButton("Edición de ingresos")
            self.btn_edicion.clicked.connect(self.abrir_edicion)
            layout.addWidget(self.btn_edicion)

        layout_registro.addWidget(self.label_patente)
        layout_registro.addWidget(self.input_patente)
        layout_registro.addWidget(self.boton_buscar)
        layout_registro.addWidget(self.info_label)
        layout_registro.addWidget(self.boton_ingreso)
        layout_registro.addWidget(self.boton_salida)
        layout_registro.addWidget(self.boton_espera)
        grupo_registro.setLayout(layout_registro)
        layout.addWidget(self.boton_bano)

        layout.addWidget(grupo_registro)

        # Botón para dashboard
        layout.addSpacing(10)
        self.boton_resumen = QPushButton("📊 Ver Resumen Diario")
        self.boton_resumen.clicked.connect(self.abrir_dashboard)
        layout.addWidget(self.boton_resumen)

        # Grupo para tabla de vehículos activos
        self.grupo_tabla = QGroupBox("🚗 Vehículos actualmente estacionados")
        self.grupo_tabla.setVisible(False)

        layout_tabla = QVBoxLayout()
        layout_tabla.setContentsMargins(10, 20, 10, 20)

        self.tabla_activos = QTableWidget()
        self.tabla_activos.setColumnCount(4)
        self.tabla_activos.setHorizontalHeaderLabels(["Patente", "Hora Ingreso", "Minutos", "Monto Actual"])
        self.tabla_activos.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tabla_activos.setMaximumHeight(200)

        # Estilo y resize
        self.tabla_activos.horizontalHeader().setStretchLastSection(True)
        self.tabla_activos.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla_activos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla_activos.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabla_activos.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

        layout_tabla.addWidget(self.tabla_activos)
        self.grupo_tabla.setLayout(layout_tabla)
        layout.addWidget(self.grupo_tabla)

        # Timer para actualizar
        self.timer_tabla = QTimer()
        self.timer_tabla.timeout.connect(self.actualizar_tabla_activos)
        self.timer_tabla.start(5000)
        self.actualizar_tabla_activos()

        self.setLayout(layout)

    def buscar_vehiculo(self):
        """Busca el estado del vehículo por patente e indica si puede ingresar o salir."""
        patente = self.input_patente.text().strip().upper()

        if not patente:
            QMessageBox.warning(self, "Atención", "Ingresa una patente.")
            return

        estado = buscar_estado_vehiculo(patente)
        self.info_label.setText("")

        if estado == "no_registrado":
            self.info_label.setText("Vehículo no registrado. Se creará al ingresar.")
            self.boton_ingreso.setEnabled(True)
            self.boton_salida.setEnabled(False)
            self.boton_espera.setEnabled(False)  # ← NO existe aún, no se permite poner en espera

        elif estado == "dentro":
            self.info_label.setText("Vehículo actualmente en el estacionamiento.")
            self.boton_salida.setEnabled(True)
            self.boton_ingreso.setEnabled(False)
            self.boton_espera.setEnabled(True)  # ← SOLO aquí se permite poner en espera

        elif estado == "fuera":
            self.info_label.setText("Vehículo ya salió. Puedes registrar nuevo ingreso.")
            self.boton_ingreso.setEnabled(True)
            self.boton_salida.setEnabled(False)
            self.boton_espera.setEnabled(False)  # ← Ya no está, no se puede poner en espera

        else:
            self.info_label.setText("Estado desconocido.")
            self.boton_ingreso.setEnabled(False)
            self.boton_salida.setEnabled(False)
            self.boton_espera.setEnabled(False)
            QMessageBox.critical(self, "Error", "Error al consultar la patente.")

    def registrar_ingreso(self):
        """Registra el ingreso del vehículo."""
        patente = self.input_patente.text().strip().upper()
        exito = registrar_ingreso(patente)
        if exito:
            QMessageBox.information(self, "Éxito", f"Ingreso registrado para {patente}")
            self.reset()
        else:
            QMessageBox.critical(self, "Error", "No se pudo registrar el ingreso.")
        self.actualizar_tabla_activos()

    def registrar_salida(self):
        """Registra la salida del vehículo y muestra la tarifa aplicada."""
        patente = self.input_patente.text().strip().upper()
        tarifa = registrar_salida(patente, self.usuario)  # ← aquí se pasa el usuario
        if tarifa is not None:
            QMessageBox.information(self, "Salida registrada", f"Tarifa: ${tarifa:.0f}")
            self.reset()
        else:
            QMessageBox.critical(self, "Error", "No se pudo registrar la salida.")
        self.actualizar_tabla_activos()

    def reset(self):
        """Resetea el formulario de registro."""
        self.input_patente.clear()
        self.boton_ingreso.setEnabled(False)
        self.boton_salida.setEnabled(False)
        self.info_label.setText("")

    def abrir_dashboard(self):
        """Abre la ventana del dashboard."""
        self.dashboard = DashboardWindow(self.usuario, rol="operador")  # o self.rol si lo tienes
        self.dashboard.show()

    def actualizar_tabla_activos(self):
        """Actualiza la tabla de vehículos actualmente estacionados."""
        datos = obtener_vehiculos_activos()
        self.tabla_activos.setRowCount(len(datos) + 1)
        total = 0

        for i, vehiculo in enumerate(datos):
            patente = vehiculo["patente"]
            hora = vehiculo["hora"]
            monto = vehiculo["monto"]
            print(f"DEBUG - hora: {hora} ({type(hora)})")

            try:
                hoy = datetime.now().date()  # Fecha actual
                hora_dt = datetime.strptime(hora, "%Y-%m-%d %H:%M:%S").time()  # Convierte la hora a tipo time
                hora_ingreso = datetime.combine(hoy, hora_dt)  # Une fecha y hora
                ahora = datetime.now()
                minutos = int((ahora - hora_ingreso).total_seconds() // 60)
                if minutos < 0:
                    minutos = 0  # Por si ocurre desfase horario o ingreso del día anterior
            except Exception as e:
                print(f"[ERROR al calcular minutos] {hora} → {e}")
                minutos = 0

            item_patente = QTableWidgetItem(patente)
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

        # Limpiar columnas anteriores (col 0 y 1)
        self.tabla_activos.setItem(fila_total, 0, QTableWidgetItem(""))
        self.tabla_activos.setItem(fila_total, 1, QTableWidgetItem(""))

        # Mostrar grupo solo si hay vehículos
        self.grupo_tabla.setVisible(len(datos) > 0)

    def abrir_edicion(self):
        self.ventana_edicion = EdicionIngresosWindow(self.usuario)
        self.ventana_edicion.show()

    def marcar_en_espera(self):
        """Marca el vehículo como 'en espera' si está estacionado."""
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
        """Muestra opciones para registrar uso de baño con diferentes montos."""
        from PySide6.QtWidgets import QInputDialog

        opciones = ["$300", "$400", "$500"]
        monto_str, ok = QInputDialog.getItem(
            self, "Registrar Baño", "Seleccione el monto:", opciones, 0, False
        )
        if ok and monto_str:
            monto = int(monto_str.replace("$", ""))
            from controllers.registro_controller import registrar_uso_bano
            exito = registrar_uso_bano(monto, self.usuario)
            if exito:
                QMessageBox.information(self, "Éxito", f"Uso de baño registrado por ${monto}")
            else:
                QMessageBox.critical(self, "Error", "No se pudo registrar el uso del baño.")
