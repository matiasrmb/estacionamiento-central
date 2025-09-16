from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QMessageBox
)
from PySide6.QtCore import QDate, QDateTime, QTimer, Qt
from controllers.dashboard_controller import obtener_resumen_diario
from controllers.cierres_controller import realizar_cierre_diario
from datetime import datetime

class DashboardWindow(QWidget):
    """
    Ventana de resumen diario del estacionamiento.
    Muestra estadísticas del día, como ingresos, vehículos estacionados y recaudación.
    También permite realizar el cierre diario.
    """
    def __init__(self, usuario, rol):
        super().__init__()
        self.usuario = usuario
        self.rol = rol
        self.setWindowTitle("Resumen Diario - Estacionamiento Central")
        self.setFixedSize(400, 300)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Fecha actual
        fecha = QDate.currentDate().toString("dd/MM/yyyy")
        label_fecha = QLabel(f"📅 Fecha: {fecha}")
        label_fecha.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_fecha)

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

        # Estadísticas del día
        self.label_ingresos = QLabel()
        self.label_estacionados = QLabel()
        self.label_recaudado = QLabel()

        for label in [self.label_ingresos, self.label_estacionados, self.label_recaudado]:
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-weight: bold;")

        layout.addWidget(self.label_ingresos)
        layout.addWidget(self.label_estacionados)
        layout.addWidget(self.label_recaudado)

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

    def actualizar_hora(self):
        """Actualiza el label de hora con la hora actual cada segundo."""
        hora_actual = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.label_hora.setText(f"🕒 Hora actual: {hora_actual}")

    def actualizar_resumen(self):
        """Consulta el resumen del día y actualiza las etiquetas de estadísticas."""
        resumen = obtener_resumen_diario()
        self.label_ingresos.setText(f"🚗 Ingresos hoy: {resumen['total_ingresos']}")
        self.label_estacionados.setText(f"🚘 Estacionados actualmente: {resumen['estacionados']}")
        self.label_recaudado.setText(f"💰 Total recaudado hoy: ${resumen['recaudado']:.0f}")

    def abrir_menu(self):
        """Oculta el dashboard y muestra la ventana principal del sistema."""
        from views.main_window import MainWindow
        self.hide()
        self.main = MainWindow(self.usuario, self.rol)
        self.main.show()

    def confirmar_cierre_diario(self):
        """
        Muestra una ventana de confirmación para realizar el cierre diario.
        Si el usuario confirma, realiza el cierre y muestra un mensaje con el resultado.
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
                self.actualizar_resumen()
            else:
                QMessageBox.information(self, "Sin registros", mensaje)

