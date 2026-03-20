from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout,
    QHBoxLayout, QMessageBox, QStackedWidget,
    QSizePolicy, QFrame
)
from PySide6.QtCore import Qt

from views.registro import RegistroWindow
from views.reportes import ReportesWindow
from views.mensuales import MensualesWindow
from views.configuracion import ConfiguracionWindow
from views.tarifas_personalizadas import TarifasPersonalizadasWindow
from views.usuarios import UsuariosWindow
from views.asistencias import AsistenciasWindow
from views.dashboard import DashboardWindow
from controllers.login_controller import registrar_asistencia_salida


class MainWindow(QWidget):
    """
    Ventana principal contenedora del sistema.
    Usa navegación interna con QStackedWidget para evitar abrir múltiples
    ventanas separadas.
    """

    def __init__(self, usuario, rol):
        super().__init__()
        self.usuario = usuario
        self.rol = rol

        self.setWindowTitle("Estacionamiento Central - Panel Principal")
        self.setMinimumSize(1280, 720)

        self.init_ui()
        self.showMaximized()

    def init_ui(self):
        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # =========================================================
        # SIDEBAR
        # =========================================================
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(260)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(12)

        titulo = QLabel("Estacionamiento Central")
        titulo.setObjectName("TituloVentana")
        titulo.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(titulo)

        subtitulo = QLabel(f"{self.usuario} ({self.rol})")
        subtitulo.setObjectName("SubtituloSeccion")
        subtitulo.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(subtitulo)

        self.btn_dashboard = QPushButton("🏠 Panel principal")
        self.btn_registro = QPushButton("🚗 Registro de vehículos")
        self.btn_reportes = QPushButton("📊 Reportes")
        self.btn_mensuales = QPushButton("👥 Clientes mensuales")
        self.btn_config = QPushButton("⚙️ Configuración")
        self.btn_tarifas = QPushButton("📈 Tarifas personalizadas")
        self.btn_usuarios = QPushButton("🔐 Gestión de usuarios")
        self.btn_asistencias = QPushButton("🕒 Asistencias")
        self.btn_cerrar_sesion = QPushButton("🔙 Cerrar sesión")

        botones_sidebar = [
            self.btn_dashboard,
            self.btn_registro,
        ]

        if self.rol == "administrador":
            botones_sidebar.extend([
                self.btn_reportes,
                self.btn_mensuales,
                self.btn_config,
                self.btn_tarifas,
                self.btn_usuarios,
                self.btn_asistencias,
            ])

        for btn in botones_sidebar:
            btn.setMinimumHeight(42)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding-left: 12px;
                    font-size: 14px;
                }
            """)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        self.btn_cerrar_sesion.setMinimumHeight(40)
        self.btn_cerrar_sesion.setObjectName("BotonPeligro")
        sidebar_layout.addWidget(self.btn_cerrar_sesion)

        # =========================================================
        # ÁREA DE CONTENIDO
        # =========================================================
        contenedor = QFrame()
        contenedor_layout = QVBoxLayout(contenedor)
        contenedor_layout.setContentsMargins(20, 20, 20, 20)
        contenedor_layout.setSpacing(10)

        self.label_modulo = QLabel("Panel principal")
        self.label_modulo.setContentsMargins(4, 0, 0, 10)
        self.label_modulo.setObjectName("TituloVentana")
        self.label_modulo.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        contenedor_layout.addWidget(self.label_modulo)

        self.stack = QStackedWidget()
        contenedor_layout.addWidget(self.stack)

        # =========================================================
        # VISTAS
        # =========================================================
        self.dashboard_view = DashboardWindow(
            self.usuario,
            self.rol,
            on_ir_panel=self.mostrar_dashboard
        )

        self.registro_view = RegistroWindow(
            self.usuario,
            self.rol,
            on_volver_panel=self.mostrar_dashboard
        )

        self.reportes_view = ReportesWindow()
        self.mensuales_view = MensualesWindow()
        self.config_view = ConfiguracionWindow()
        self.tarifas_view = TarifasPersonalizadasWindow()
        self.usuarios_view = UsuariosWindow()
        self.asistencias_view = AsistenciasWindow()

        self.stack.addWidget(self.dashboard_view)
        self.stack.addWidget(self.registro_view)
        self.stack.addWidget(self.reportes_view)
        self.stack.addWidget(self.mensuales_view)
        self.stack.addWidget(self.config_view)
        self.stack.addWidget(self.tarifas_view)
        self.stack.addWidget(self.usuarios_view)
        self.stack.addWidget(self.asistencias_view)

        # =========================================================
        # CONEXIONES
        # =========================================================
        self.btn_dashboard.clicked.connect(self.mostrar_dashboard)
        self.btn_registro.clicked.connect(self.mostrar_registro)

        if self.rol == "administrador":
            self.btn_reportes.clicked.connect(self.mostrar_reportes)
            self.btn_mensuales.clicked.connect(self.mostrar_mensuales)
            self.btn_config.clicked.connect(self.mostrar_configuracion)
            self.btn_tarifas.clicked.connect(self.mostrar_tarifas)
            self.btn_usuarios.clicked.connect(self.mostrar_usuarios)
            self.btn_asistencias.clicked.connect(self.mostrar_asistencias)

        self.btn_cerrar_sesion.clicked.connect(self.cerrar_sesion)

        layout_principal.addWidget(sidebar)
        layout_principal.addWidget(contenedor)

        self.mostrar_dashboard()

    # =========================================================
    # NAVEGACIÓN
    # =========================================================
    def mostrar_dashboard(self):
        self.label_modulo.setText("Panel principal")
        self.stack.setCurrentWidget(self.dashboard_view)

    def mostrar_registro(self):
        self.label_modulo.setText("Registro de vehículos")
        self.stack.setCurrentWidget(self.registro_view)

    def mostrar_reportes(self):
        self.label_modulo.setText("Reportes")
        self.stack.setCurrentWidget(self.reportes_view)

    def mostrar_mensuales(self):
        self.label_modulo.setText("Clientes mensuales")
        self.stack.setCurrentWidget(self.mensuales_view)

    def mostrar_configuracion(self):
        self.label_modulo.setText("Configuración")
        self.stack.setCurrentWidget(self.config_view)

    def mostrar_tarifas(self):
        self.label_modulo.setText("Tarifas personalizadas")
        self.stack.setCurrentWidget(self.tarifas_view)

    def mostrar_usuarios(self):
        self.label_modulo.setText("Gestión de usuarios")
        self.stack.setCurrentWidget(self.usuarios_view)

    def mostrar_asistencias(self):
        self.label_modulo.setText("Asistencias")
        self.stack.setCurrentWidget(self.asistencias_view)

    # =========================================================
    # SESIÓN
    # =========================================================
    def cerrar_sesion(self):
        """
        Registra la salida del usuario y cierra la ventana principal mostrando un resumen.
        """
        resumen = registrar_asistencia_salida(self.usuario)

        QMessageBox.information(
            self,
            "Resumen del día",
            f"Sesión: {resumen['hora_inicio'].strftime('%d-%m-%Y %H:%M') if resumen['hora_inicio'] else 'N/A'} - ahora\n"
            f"Vehículos cobrados: {resumen['cantidad']}\n"
            f"Total recaudado: ${resumen['total']:.0f}"
        )
        self.close()