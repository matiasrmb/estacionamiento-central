from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QMessageBox
)

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

        # Botones de navegación
        btn_ingreso = QPushButton("Registrar Ingreso")
        btn_salida = QPushButton("Registrar Salida")
        btn_reportes = QPushButton("Reportes")

        # Comportamiento por rol
        if self.rol != "administrador":
            btn_reportes.setDisabled(True)

        # Agrega botones al layout
        layout.addWidget(btn_ingreso)
        layout.addWidget(btn_salida)
        layout.addWidget(btn_reportes)

        # Salir
        btn_salir = QPushButton("Cerrar sesión")
        btn_salir.clicked.connect(self.close)
        layout.addWidget(btn_salir)

        self.setLayout(layout)