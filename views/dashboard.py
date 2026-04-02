from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QMessageBox,
    QGridLayout, QFrame, QSizePolicy, QHBoxLayout
)
from PySide6.QtCore import QDateTime, QTimer, Qt

from controllers.dashboard_controller import obtener_resumen_diario, obtener_resumen_banos
from controllers.cierres_controller import realizar_cierre_diario
from utils.db import get_connection
from datetime import datetime


class DashboardWindow(QWidget):
    """
    Vista de resumen diario del estacionamiento.
    Muestra estadísticas del turno actual y permite realizar el cierre diario.
    """

    def __init__(self, usuario, rol, on_ir_panel=None, on_ir_registro=None, on_ir_reportes=None):
        super().__init__()
        self.usuario = usuario
        self.rol = rol
        self.on_ir_panel = on_ir_panel
        self.on_ir_registro = on_ir_registro
        self.on_ir_reportes = on_ir_reportes

        self.actualizacion_habilitada = True
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # =========================================================
        # ENCABEZADO
        # =========================================================

        self.label_periodo = QLabel(self.obtener_periodo_resumen())
        self.label_periodo.setObjectName("SubtituloSeccion")
        self.label_periodo.setAlignment(Qt.AlignLeft)
        self.label_periodo.setWordWrap(True)
        layout.addWidget(self.label_periodo)

        self.label_hora = QLabel()
        self.label_hora.setAlignment(Qt.AlignLeft)
        self.label_hora.setWordWrap(True)
        layout.addWidget(self.label_hora)

        self.label_usuario = QLabel(f"Usuario activo: {self.usuario} ({self.rol})")
        self.label_usuario.setAlignment(Qt.AlignLeft)
        self.label_usuario.setWordWrap(True)
        layout.addWidget(self.label_usuario)

        # =========================================================
        # TARJETAS DE RESUMEN
        # =========================================================
        grid_resumen = QGridLayout()
        grid_resumen.setHorizontalSpacing(12)
        grid_resumen.setVerticalSpacing(12)

        self.card_ingresos = self.crear_tarjeta("Ingresos del turno", "0")
        self.card_estacionados = self.crear_tarjeta("Vehículos estacionados", "0")
        self.card_recaudado = self.crear_tarjeta("Recaudado vehículos", "$0")
        self.card_banos = self.crear_tarjeta("Usos de baño", "0 | $0")
        self.card_total = self.crear_tarjeta("Total general", "$0")

        grid_resumen.addWidget(self.card_ingresos["frame"], 0, 0)
        grid_resumen.addWidget(self.card_estacionados["frame"], 0, 1)
        grid_resumen.addWidget(self.card_recaudado["frame"], 1, 0)
        grid_resumen.addWidget(self.card_banos["frame"], 1, 1)
        grid_resumen.addWidget(self.card_total["frame"], 2, 0, 1, 2)

        grid_resumen.setColumnStretch(0, 1)
        grid_resumen.setColumnStretch(1, 1)

        layout.addLayout(grid_resumen)

        # =========================================================
        # ACCIONES PRINCIPALES
        # =========================================================
        acciones_layout = QHBoxLayout()
        acciones_layout.setSpacing(10)

        self.boton_cierre = QPushButton("Realizar cierre diario")
        self.boton_cierre.setMinimumHeight(42)
        self.boton_cierre.clicked.connect(self.confirmar_cierre_diario)

        acciones_layout.addWidget(self.boton_cierre)
        acciones_layout.addStretch()

        layout.addLayout(acciones_layout)

        # =========================================================
        # ACCESOS RÁPIDOS
        # =========================================================
        accesos_titulo = QLabel("Accesos rápidos")
        accesos_titulo.setObjectName("SubtituloSeccion")
        accesos_titulo.setAlignment(Qt.AlignLeft)
        layout.addWidget(accesos_titulo)

        accesos_layout = QHBoxLayout()
        accesos_layout.setSpacing(10)

        self.btn_ir_registro = QPushButton("Ir a registro")
        self.btn_ir_registro.setMinimumHeight(40)
        self.btn_ir_registro.clicked.connect(self.ir_a_registro)
        accesos_layout.addWidget(self.btn_ir_registro)

        if self.rol == "administrador":
            self.btn_ir_reportes = QPushButton("Ir a reportes")
            self.btn_ir_reportes.setMinimumHeight(40)
            self.btn_ir_reportes.clicked.connect(self.ir_a_reportes)
            accesos_layout.addWidget(self.btn_ir_reportes)

        accesos_layout.addStretch()
        layout.addLayout(accesos_layout)

        layout.addStretch()
        self.setLayout(layout)

        # Timers
        self.timer = QTimer()
        self.timer.timeout.connect(self.actualizar_hora)
        self.timer.start(1000)
        self.actualizar_hora()

        self.timer_resumen = QTimer()
        self.timer_resumen.timeout.connect(self.actualizar_resumen)
        self.timer_resumen.start(1000)

        self.actualizar_resumen()

    def crear_tarjeta(self, titulo, valor):
        frame = QFrame()
        frame.setObjectName("TarjetaResumen")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        frame.setMinimumHeight(110)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("TituloResumenModulo")
        label_titulo.setWordWrap(True)

        label_valor = QLabel(valor)
        label_valor.setObjectName("ValorResumenModulo")
        label_valor.setWordWrap(True)

        layout.addWidget(label_titulo)
        layout.addWidget(label_valor)
        layout.addStretch()

        return {
            "frame": frame,
            "titulo": label_titulo,
            "valor": label_valor
        }

    def actualizar_hora(self):
        hora_actual = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.label_hora.setText(f"Hora actual: {hora_actual}")

    def obtener_periodo_resumen(self):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT MAX(fecha_cierre) AS ultima_cierre FROM cierres_diarios")
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row and row["ultima_cierre"]:
            fecha_inicio = row["ultima_cierre"].strftime("%d/%m/%Y %H:%M")
        else:
            fecha_inicio = "Inicio del sistema"

        fecha_fin = datetime.now().strftime("%d/%m/%Y %H:%M")
        return f"Período del turno: {fecha_inicio} → {fecha_fin}"

    def actualizar_resumen(self):
        if not self.actualizacion_habilitada:
            return

        resumen = obtener_resumen_diario()
        resumen_banos = obtener_resumen_banos()
        recaudacion_total = resumen["recaudado"] + resumen_banos["total"]

        self.card_ingresos["valor"].setText(str(resumen["total_ingresos"]))
        self.card_estacionados["valor"].setText(str(resumen["estacionados"]))
        self.card_recaudado["valor"].setText(f"${resumen['recaudado']:.0f}")
        self.card_banos["valor"].setText(f"{resumen_banos['cantidad']} | ${resumen_banos['total']:.0f}")
        self.card_total["valor"].setText(f"${recaudacion_total:.0f}")

        self.label_periodo.setText(self.obtener_periodo_resumen())

        if resumen["total_ingresos"] > 0 or resumen_banos["cantidad"] > 0 or resumen["recaudado"] > 0:
            self.actualizacion_habilitada = True

    def confirmar_cierre_diario(self):
        respuesta = QMessageBox.question(
            self,
            "Confirmar cierre diario",
            "¿Estás seguro de que deseas realizar el cierre diario?\nEsto marcará como cerradas todas las salidas registradas hasta ahora.",
            QMessageBox.Yes | QMessageBox.No
        )
        if respuesta == QMessageBox.Yes:
            exito, mensaje = realizar_cierre_diario(self.usuario)
            if exito:
                QMessageBox.information(self, "Éxito", mensaje)

                self.card_ingresos["valor"].setText("0")
                self.card_estacionados["valor"].setText("0")
                self.card_recaudado["valor"].setText("$0")
                self.card_banos["valor"].setText("0 | $0")
                self.card_total["valor"].setText("$0")
                self.label_periodo.setText(self.obtener_periodo_resumen())
                self.actualizacion_habilitada = False
            else:
                QMessageBox.information(self, "Sin registros", mensaje)

    def ir_a_registro(self):
        if callable(self.on_ir_registro):
            self.on_ir_registro()

    def ir_a_reportes(self):
        if callable(self.on_ir_reportes):
            self.on_ir_reportes()