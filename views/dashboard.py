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
    Ventana de resumen diario del estacionamiento.
    Muestra estadísticas del turno actual (desde el último cierre hasta ahora).
    También permite realizar el cierre diario.
    """
    def __init__(self, usuario, rol):
        super().__init__()
        self.usuario = usuario
        self.rol = rol
        self.setWindowTitle("Resumen Diario - Estacionamiento Central")
        self.setFixedSize(500, 420)
        self.actualizacion_habilitada = True
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Mostrar período del resumen (desde último cierre hasta ahora)
        periodo_texto = self.obtener_periodo_resumen()
        self.label_periodo = QLabel(periodo_texto)
        self.label_periodo.setAlignment(Qt.AlignCenter)
        self.label_periodo.setStyleSheet("font-size: 13px; color: gray;")
        layout.addWidget(self.label_periodo)

        # Hora actual
        self.label_hora = QLabel()
        self.label_hora.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_hora)

        self.timer = QTimer()
        self.timer.timeout.connect(self.actualizar_hora)
        self.timer.start(1000)
        self.actualizar_hora()

        # Usuario y rol
        label_usuario = QLabel(f"🧍 Usuario: {self.usuario} ({self.rol})")
        label_usuario.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_usuario)

        # Estadísticas del turno
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

        # Botón para realizar cierre diario
        self.boton_cierre = QPushButton("📦 Realizar Cierre Diario")
        self.boton_cierre.setMinimumHeight(35)
        self.boton_cierre.clicked.connect(self.confirmar_cierre_diario)
        layout.addWidget(self.boton_cierre)

        # Botón para continuar al panel principal
        self.btn_continuar = QPushButton("Ir al Panel Principal")
        self.btn_continuar.setMinimumHeight(30)
        self.btn_continuar.clicked.connect(self.abrir_menu)
        layout.addWidget(self.btn_continuar)

        self.setLayout(layout)

        # Timer para refrescar estadísticas en tiempo real
        self.timer_resumen = QTimer()
        self.timer_resumen.timeout.connect(self.actualizar_resumen)
        self.timer_resumen.start(1000)  # Cada 1 segundo

    def actualizar_hora(self):
        """Actualiza el label de hora con la hora actual cada segundo."""
        hora_actual = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.label_hora.setText(f"🕒 Hora actual: {hora_actual}")

    def obtener_periodo_resumen(self):
        """
        Devuelve el período desde el último cierre diario hasta ahora
        en formato amigable.
        """
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
        """
        Consulta el resumen del turno y actualiza las etiquetas de estadísticas,
        incluyendo ingresos, estacionados, recaudación y uso de baños.
        """
        if not self.actualizacion_habilitada:
            return  # Si se deshabilitó, no consultar DB

        resumen = obtener_resumen_diario()
        resumen_banos = obtener_resumen_banos()
        recaudacion_total = resumen["recaudado"] + resumen_banos["total"]

        self.label_ingresos.setText(f"🚗 Ingresos: {resumen['total_ingresos']}")
        self.label_estacionados.setText(f"🚘 Estacionados actualmente: {resumen['estacionados']}")
        self.label_recaudado.setText(f"💰 Recaudado vehículos: ${resumen['recaudado']:.0f}")
        self.label_banos.setText(f"🚽 Baños: {resumen_banos['cantidad']} usos, ${resumen_banos['total']:.0f}")
        self.label_total_general.setText(f"📊 Total general: ${recaudacion_total:.0f}")

        # Refrescar período mostrado
        self.label_periodo.setText(self.obtener_periodo_resumen())

        # Si detecta un nuevo movimiento, reactivar auto-actualización
        if resumen["total_ingresos"] > 0 or resumen_banos["cantidad"] > 0 or resumen["recaudado"] > 0:
            self.actualizacion_habilitada = True

    def abrir_menu(self):
        """Oculta el dashboard y muestra la ventana principal del sistema."""
        from views.main_window import MainWindow
        self.hide()
        self.main = MainWindow(self.usuario, self.rol)
        self.main.show()

    def confirmar_cierre_diario(self):
        """
        Muestra una ventana de confirmación para realizar el cierre diario.
        Si el usuario confirma, realiza el cierre y reinicia los labels.
        """
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

                # Reinicia manualmente los labels
                self.label_ingresos.setText("🚗 Ingresos: 0")
                self.label_estacionados.setText("🚘 Estacionados actualmente: 0")
                self.label_recaudado.setText("💰 Recaudado vehículos: $0")
                self.label_banos.setText("🚽 Baños: 0 usos, $0")
                self.label_total_general.setText("📊 Total general: $0")
                self.label_periodo.setText(self.obtener_periodo_resumen())
                self.actualizacion_habilitada = False
            else:
                QMessageBox.information(self, "Sin registros", mensaje)
