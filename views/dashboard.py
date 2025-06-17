from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton
from PySide6.QtCore import QDate, QDateTime, QTimer
from controllers.dashboard_controller import obtener_resumen_diario

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
        layout.addWidget(QLabel(f"🚗 Ingresos hoy: {resumen['total_ingresos']}"))
        layout.addWidget(QLabel(f"🚘 Estacionados actualmente: {resumen['estacionados']}"))
        layout.addWidget(QLabel(f"💰 Total recaudado hoy: ${resumen['recaudado']:.0f}"))

        self.btn_continuar = QPushButton("Ir al Panel Principal")
        self.btn_continuar.clicked.connect(self.abrir_menu)
        layout.addWidget(self.btn_continuar)

        self.setLayout(layout)

    def actualizar_hora(self):
        hora_actual = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.label_hora.setText(f"🕒 Hora actual: {hora_actual}")

    def abrir_menu(self):
        from views.main_window import MainWindow
        self.hide()
        self.main = MainWindow(self.usuario, self.rol)
        self.main.show()
