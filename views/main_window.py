from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout
)
from views.registro import RegistroWindow
from views.reportes import ReportesWindow
from views.mensuales import MensualesWindow
from views.configuracion import ConfiguracionWindow

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

        # Botón de agregar mensuales (solo para admin)
        if self.rol == "administrador":
            btn_mensuales = QPushButton("Clientes Mensuales")
            btn_mensuales.clicked.connect(self.abrir_mensuales)
            layout.addWidget(btn_mensuales)

        # Botón para configuración (solo para admin)
        if self.rol == "administrador":
            btn_config = QPushButton("Configuración")
            btn_config.clicked.connect(self.abrir_configuracion)
            layout.addWidget(btn_config)

        # Botón de reportes (solo para admin)
        btn_reportes = QPushButton("Reportes")
        btn_reportes.clicked.connect(self.abrir_reportes)
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

    def abrir_reportes(self):
        self.reportes_window = ReportesWindow()
        self.reportes_window.show()
        
    def abrir_mensuales(self):
        self.mensuales_window = MensualesWindow()
        self.mensuales_window.show()

    def abrir_configuracion(self):
        self.config_window = ConfiguracionWindow()
        self.config_window.show()
