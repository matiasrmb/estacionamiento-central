from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QMessageBox
)
from PySide6.QtCore import QDateTime, QTimer, Qt

from controllers.dashboard_controller import obtener_resumen_diario, obtener_resumen_banos
from controllers.cierres_controller import realizar_cierre_diario
from utils.db import get_connection
from datetime import datetime


class DashboardWindow(QWidget):
    """
    Vista de resumen diario del estacionamiento.
    Muestra estadísticas del turno actual (desde el último cierre hasta ahora)
    y permite realizar el cierre diario.
    """

    def __init__(self, usuario, rol, on_ir_panel=None):
        super().__init__()
        self.usuario = usuario
        self.rol = rol
        self.on_ir_panel = on_ir_panel

        self.actualizacion_habilitada = True
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        titulo = QLabel("📊 Resumen diario")
        titulo.setObjectName("TituloVentana")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        periodo_texto = self.obtener_periodo_resumen()
        self.label_periodo = QLabel(periodo_texto)
        self.label_periodo.setAlignment(Qt.AlignCenter)
        self.label_periodo.setStyleSheet("font-size: 13px; color: gray;")
        layout.addWidget(self.label_periodo)

        self.label_hora = QLabel()
        self.label_hora.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_hora)

        self.timer = QTimer()
        self.timer.timeout.connect(self.actualizar_hora)
        self.timer.start(1000)
        self.actualizar_hora()

        label_usuario = QLabel(f"🧍 Usuario: {self.usuario} ({self.rol})")
        label_usuario.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_usuario)

        self.label_ingresos = QLabel()
        self.label_estacionados = QLabel()
        self.label_recaudado = QLabel()
        self.label_banos = QLabel()
        self.label_total_general = QLabel()

        for label in [
            self.label_ingresos,
            self.label_estacionados,
            self.label_recaudado,
            self.label_banos,
            self.label_total_general
        ]:
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-weight: bold;")
            layout.addWidget(label)

        self.actualizar_resumen()

        self.boton_cierre = QPushButton("📦 Realizar Cierre Diario")
        self.boton_cierre.setMinimumHeight(35)
        self.boton_cierre.clicked.connect(self.confirmar_cierre_diario)
        layout.addWidget(self.boton_cierre)

        self.setLayout(layout)

        self.timer_resumen = QTimer()
        self.timer_resumen.timeout.connect(self.actualizar_resumen)
        self.timer_resumen.start(1000)

    def actualizar_hora(self):
        hora_actual = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.label_hora.setText(f"🕒 Hora actual: {hora_actual}")

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
        return f"📅 Período: {fecha_inicio} → {fecha_fin}"

    def actualizar_resumen(self):
        if not self.actualizacion_habilitada:
            return

        resumen = obtener_resumen_diario()
        resumen_banos = obtener_resumen_banos()
        recaudacion_total = resumen["recaudado"] + resumen_banos["total"]

        self.label_ingresos.setText(f"🚗 Ingresos: {resumen['total_ingresos']}")
        self.label_estacionados.setText(f"🚘 Estacionados actualmente: {resumen['estacionados']}")
        self.label_recaudado.setText(f"💰 Recaudado vehículos: ${resumen['recaudado']:.0f}")
        self.label_banos.setText(f"🚽 Baños: {resumen_banos['cantidad']} usos, ${resumen_banos['total']:.0f}")
        self.label_total_general.setText(f"📊 Total general: ${recaudacion_total:.0f}")

        self.label_periodo.setText(self.obtener_periodo_resumen())

        if resumen["total_ingresos"] > 0 or resumen_banos["cantidad"] > 0 or resumen["recaudado"] > 0:
            self.actualizacion_habilitada = True

    def confirmar_cierre_diario(self):
        respuesta = QMessageBox.question(
            self,
            "Confirmar Cierre Diario",
            "¿Estás seguro de que deseas realizar el cierre diario?\nEsto marcará como cerradas todas las salidas registradas hasta ahora.",
            QMessageBox.Yes | QMessageBox.No
        )
        if respuesta == QMessageBox.Yes:
            exito, mensaje = realizar_cierre_diario(self.usuario)
            if exito:
                QMessageBox.information(self, "Éxito", mensaje)

                self.label_ingresos.setText("🚗 Ingresos: 0")
                self.label_estacionados.setText("🚘 Estacionados actualmente: 0")
                self.label_recaudado.setText("💰 Recaudado vehículos: $0")
                self.label_banos.setText("🚽 Baños: 0 usos, $0")
                self.label_total_general.setText("📊 Total general: $0")
                self.label_periodo.setText(self.obtener_periodo_resumen())
                self.actualizacion_habilitada = False
            else:
                QMessageBox.information(self, "Sin registros", mensaje)