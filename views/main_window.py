from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout
)
from views.registro import RegistroWindow

class MainWindow(QWidget):
    def __init__(self, usuario, rol):
        super().__init__()
        self.usuario = usuario
        self.rol = rol
        self.setWindowTitle("Estacionamiento Central - Panel Principal")
        self.setFixedSize(400, 300)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        bienvenida = QLabel(f"Bienvenido, {self.usuario} ({self.rol})")
        layout.addWidget(bienvenida)

        # Botón de registro de vehículos
        btn_registro = QPushButton("Registro de Vehículos")
        btn_registro.clicked.connect(self.abrir_registro)
        layout.addWidget(btn_registro)

        # Botón de reportes (solo para administrador)
        btn_reportes = QPushButton("Reportes")
        if self.rol != "administrador":
            btn_reportes.setDisabled(True)
        layout.addWidget(btn_reportes)

        # Botón de cierre de sesión
        btn_salir = QPushButton("Cerrar sesión")
        btn_salir.clicked.connect(self.close)
        layout.addWidget(btn_salir)

        self.setLayout(layout)

    def abrir_registro(self):
        self.registro_window = RegistroWindow(self.usuario)
        self.registro_window.show()
