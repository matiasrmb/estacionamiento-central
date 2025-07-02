from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QMessageBox
from PySide6.QtCore import QDate, QDateTime, QTimer
from controllers.dashboard_controller import obtener_resumen_diario
from controllers.cierres_controller import realizar_cierre_diario, realizar_cierre_mensual
from datetime import datetime

class DashboardWindow(QWidget):
    def __init__(self, usuario, rol):
        super().__init__()
        self.usuario = usuario
        self.rol = rol
        self.setWindowTitle("Resumen Diario - Estacionamiento Central")
        self.setFixedSize(400, 300)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        fecha = QDate.currentDate().toString("dd/MM/yyyy")
        resumen = obtener_resumen_diario()

        layout.addWidget(QLabel(f"📅 Fecha: {fecha}"))

        self.label_hora = QLabel()
        layout.addWidget(self.label_hora)

        self.timer = QTimer()
        self.timer.timeout.connect(self.actualizar_hora)
        self.timer.start(1000)
        self.actualizar_hora()

        layout.addWidget(self.label_hora)
        layout.addWidget(QLabel(f"🧍 Usuario: {self.usuario} ({self.rol})"))

        self.label_ingresos = QLabel()
        self.label_estacionados = QLabel()
        self.label_recaudado = QLabel()

        layout.addWidget(self.label_ingresos)
        layout.addWidget(self.label_estacionados)
        layout.addWidget(self.label_recaudado)

        self.actualizar_resumen()

        self.boton_cierre = QPushButton("📦 Realizar Cierre Diario")
        self.boton_cierre.clicked.connect(self.confirmar_cierre_diario)
        layout.addWidget(self.boton_cierre)

        self.boton_cierre_mensual = QPushButton("📆 Realizar Cierre Mensual")
        self.boton_cierre_mensual.clicked.connect(self.confirmar_cierre_mensual)
        layout.addWidget(self.boton_cierre_mensual)


        self.btn_continuar = QPushButton("Ir al Panel Principal")
        self.btn_continuar.clicked.connect(self.abrir_menu)
        layout.addWidget(self.btn_continuar)

        self.setLayout(layout)

    def actualizar_hora(self):
        hora_actual = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.label_hora.setText(f"🕒 Hora actual: {hora_actual}")

    def actualizar_resumen(self):
        resumen = obtener_resumen_diario()
        self.label_ingresos.setText(f"🚗 Ingresos hoy: {resumen['total_ingresos']}")
        self.label_estacionados.setText(f"🚘 Estacionados actualmente: {resumen['estacionados']}")
        self.label_recaudado.setText(f"💰 Total recaudado hoy: ${resumen['recaudado']:.0f}")

    def abrir_menu(self):
        from views.main_window import MainWindow
        self.hide()
        self.main = MainWindow(self.usuario, self.rol)
        self.main.show()

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
                self.actualizar_resumen()
            else:
                QMessageBox.information(self, "Sin registros", mensaje)

    def confirmar_cierre_mensual(self):
        confirmar = QMessageBox.question(
            self,
            "Confirmar Cierre Mensual",
            "¿Deseas cerrar el mes más antiguo aún no cerrado?\nEste proceso es irreversible.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirmar == QMessageBox.Yes:
            exito, mensaje = realizar_cierre_mensual(self.usuario)
            if exito:
                QMessageBox.information(self, "Éxito", mensaje)
                self.actualizar_resumen()
            else:
                QMessageBox.information(self, "Aviso", mensaje)
