from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt
from views.registro import RegistroWindow
from views.reportes import ReportesWindow
from views.mensuales import MensualesWindow
from views.configuracion import ConfiguracionWindow
from views.tarifas_personalizadas import TarifasPersonalizadasWindow
from views.usuarios import UsuariosWindow
from views.asistencias import AsistenciasWindow
from controllers.login_controller import registrar_asistencia_salida

class MainWindow(QWidget):
    def __init__(self, usuario, rol):
        super().__init__()
        self.usuario = usuario
        self.rol = rol
        self.setWindowTitle("🅿️ Estacionamiento Central - Panel Principal")
        self.setMinimumSize(420, 450)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Encabezado
        bienvenida = QLabel(f"👋 Bienvenido, <b>{self.usuario}</b> <span style='color:gray;'>({self.rol})</span>")
        bienvenida.setAlignment(Qt.AlignCenter)
        bienvenida.setStyleSheet("font-size: 16px; padding: 10px;")
        layout.addWidget(bienvenida)

        # Botones principales
        botones = [
            ("🚗 Registro de Vehículos", self.abrir_registro),
            ("📊 Reportes", self.abrir_reportes if self.rol == "administrador" else None),
            ("👥 Clientes Mensuales", self.abrir_mensuales if self.rol == "administrador" else None),
            ("⚙️ Configuración", self.abrir_configuracion if self.rol == "administrador" else None),
            ("📈 Editar tarifas personalizadas", self.abrir_tarifas if self.rol == "administrador" else None),
            ("🔐 Gestión de Usuarios", self.abrir_usuarios if self.rol == "administrador" else None),
            ("🕒 Ver asistencias", self.abrir_asistencias if self.rol == "administrador" else None)
        ]

        for texto, funcion in botones:
            btn = QPushButton(texto)
            btn.setMinimumHeight(40)
            if funcion:
                btn.clicked.connect(funcion)
            else:
                btn.setDisabled(True)
            layout.addWidget(btn)

        # Espacio flexible
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Botón de salida
        btn_salir = QPushButton("🔙 Cerrar sesión")
        btn_salir.setMinimumHeight(35)
        btn_salir.clicked.connect(self.cerrar_sesion)
        layout.addWidget(btn_salir)

        self.setLayout(layout)

    def abrir_registro(self):
        self.registro_window = RegistroWindow(self.usuario, self.rol)
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

    def abrir_tarifas(self):
        self.tarifas_window = TarifasPersonalizadasWindow()
        self.tarifas_window.show()

    def abrir_usuarios(self):
        self.usuarios_window = UsuariosWindow()
        self.usuarios_window.show()

    def abrir_asistencias(self):
        self.asistencias_window = AsistenciasWindow()
        self.asistencias_window.show()
    
    def cerrar_sesion(self):

        resumen = registrar_asistencia_salida(self.usuario)

        QMessageBox.information(
            self,
            "Resumen del día",
            f"Sesión: {resumen['hora_inicio'].strftime('%d-%m-%Y %H:%M') if resumen['hora_inicio'] else 'N/A'} - ahora\n"
            f"Vehículos cobrados: {resumen['cantidad']}\n"
            f"Total recaudado: ${resumen['total']:.0f}"
        )
        self.close()
