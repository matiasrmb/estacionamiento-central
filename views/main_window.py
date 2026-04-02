from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout,
    QHBoxLayout, QMessageBox, QStackedWidget,
    QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from views.registro import RegistroWindow
from views.reportes import ReportesWindow
from views.mensuales import MensualesWindow
from views.configuracion import ConfiguracionWindow
from views.tarifas_personalizadas import TarifasPersonalizadasWindow
from views.usuarios import UsuariosWindow
from views.asistencias import AsistenciasWindow
from views.dashboard import DashboardWindow
from views.admin_edicion import EdicionIngresosWindow
from controllers.login_controller import registrar_asistencia_salida


class MainWindow(QWidget):
    """
    Ventana principal contenedora del sistema.

    Usa navegación interna con QStackedWidget para evitar abrir múltiples
    ventanas separadas y permite contraer/expandir el sidebar para
    adaptarse mejor a escalados altos como 125%.
    """

    SIDEBAR_EXPANDED_WIDTH = 310
    SIDEBAR_COLLAPSED_WIDTH = 78
    ICON_SIZE = QSize(20, 20)

    def __init__(self, usuario, rol):
        super().__init__()
        self.usuario = usuario
        self.rol = rol
        self.sidebar_expandido = True

        self.base_dir = Path(__file__).resolve().parent.parent
        self.icons_dir = self.base_dir / "assets" / "icons"

        self.setWindowTitle("Estacionamiento Central - Panel Principal")
        self.setMinimumSize(1280, 720)

        self.init_ui()
        self.showMaximized()

    def cargar_icono(self, nombre_archivo: str) -> QIcon:
        """
        Carga un ícono desde la carpeta icons del proyecto.
        Si no existe, devuelve un ícono vacío.
        """
        ruta = self.icons_dir / nombre_archivo
        if ruta.exists():
            return QIcon(str(ruta))
        return QIcon()

    def configurar_boton_sidebar(self, boton: QPushButton, texto: str, icono: str):
        """
        Configura propiedades comunes de un botón del sidebar.
        """
        boton.setProperty("texto_expandido", texto)
        boton.setProperty("icono_archivo", icono)
        boton.setText(texto)
        boton.setIcon(self.cargar_icono(icono))
        boton.setIconSize(self.ICON_SIZE)
        boton.setMinimumHeight(42)
        boton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        boton.setCursor(Qt.PointingHandCursor)
        boton.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 12px;
                font-size: 14px;
            }
        """)

    def init_ui(self):
        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # =========================================================
        # SIDEBAR
        # =========================================================
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setMinimumWidth(self.SIDEBAR_EXPANDED_WIDTH)
        self.sidebar.setMaximumWidth(self.SIDEBAR_EXPANDED_WIDTH)
        self.sidebar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        sidebar_layout.setSpacing(10)

        header_sidebar = QHBoxLayout()
        header_sidebar.setSpacing(8)

        self.titulo_sidebar = QLabel("Estacionamiento Central")
        self.titulo_sidebar.setObjectName("TituloVentana")
        self.titulo_sidebar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.titulo_sidebar.setWordWrap(True)

        self.btn_toggle_sidebar = QPushButton()
        self.btn_toggle_sidebar.setObjectName("BotonSecundario")
        self.btn_toggle_sidebar.setFixedHeight(34)
        self.btn_toggle_sidebar.setFixedWidth(42)
        self.btn_toggle_sidebar.clicked.connect(self.toggle_sidebar)

        header_sidebar.addWidget(self.titulo_sidebar, 1)
        header_sidebar.addWidget(self.btn_toggle_sidebar, 0, alignment=Qt.AlignCenter)

        sidebar_layout.addLayout(header_sidebar)

        self.subtitulo_sidebar = QLabel(f"{self.usuario} ({self.rol})")
        self.subtitulo_sidebar.setObjectName("SubtituloSeccion")
        self.subtitulo_sidebar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.subtitulo_sidebar.setWordWrap(True)
        sidebar_layout.addWidget(self.subtitulo_sidebar)

        self.btn_dashboard = QPushButton()
        self.btn_registro = QPushButton()
        self.btn_reportes = QPushButton()
        self.btn_mensuales = QPushButton()
        self.btn_config = QPushButton()
        self.btn_tarifas = QPushButton()
        self.btn_usuarios = QPushButton()
        self.btn_asistencias = QPushButton()
        self.btn_edicion = QPushButton()
        self.btn_cerrar_sesion = QPushButton()

        self.sidebar_buttons_data = [
            (self.btn_dashboard, "Panel principal", "dashboard.svg"),
            (self.btn_registro, "Registro de vehículos", "registro.svg"),
        ]

        if self.rol == "administrador":
            self.sidebar_buttons_data.extend([
                (self.btn_reportes, "Reportes", "reportes.svg"),
                (self.btn_mensuales, "Clientes mensuales", "mensuales.svg"),
                (self.btn_config, "Configuración", "configuracion.svg"),
                (self.btn_tarifas, "Tarifas personalizadas", "tarifas.svg"),
                (self.btn_edicion, "Edición de ingresos", "edicion.svg"),
                (self.btn_usuarios, "Gestión de usuarios", "usuarios.svg"),
                (self.btn_asistencias, "Asistencias", "asistencias.svg"),
            ])

        for btn, texto, icono in self.sidebar_buttons_data:
            self.configurar_boton_sidebar(btn, texto, icono)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        self.configurar_boton_sidebar(self.btn_cerrar_sesion, "Cerrar sesión", "salir.svg")
        self.btn_cerrar_sesion.setObjectName("BotonPeligro")
        sidebar_layout.addWidget(self.btn_cerrar_sesion)

        # =========================================================
        # ÁREA DE CONTENIDO
        # =========================================================
        contenedor = QFrame()
        contenedor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        contenedor_layout = QVBoxLayout(contenedor)
        contenedor_layout.setContentsMargins(20, 20, 20, 20)
        contenedor_layout.setSpacing(8)

        self.label_modulo = QLabel("Panel principal")
        self.label_modulo.setContentsMargins(4, 0, 0, 4)
        self.label_modulo.setObjectName("TituloVentana")
        self.label_modulo.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label_modulo.setWordWrap(True)
        contenedor_layout.addWidget(self.label_modulo)

        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        contenedor_layout.addWidget(self.stack, 1)

        # =========================================================
        # VISTAS
        # =========================================================
        self.dashboard_view = DashboardWindow(
            self.usuario,
            self.rol,
            on_ir_panel=self.mostrar_dashboard,
            on_ir_registro=self.mostrar_registro,
            on_ir_reportes=self.mostrar_reportes if self.rol == "administrador" else None
        )

        self.registro_view = RegistroWindow(
            self.usuario,
            self.rol,
            on_volver_panel=self.mostrar_dashboard,
            on_ir_edicion=self.mostrar_edicion
        )

        self.reportes_view = ReportesWindow()
        self.mensuales_view = MensualesWindow()
        self.config_view = ConfiguracionWindow()
        self.tarifas_view = TarifasPersonalizadasWindow()
        self.edicion_view = EdicionIngresosWindow(
            self.usuario,
            on_volver_panel=self.mostrar_dashboard
        )
        self.usuarios_view = UsuariosWindow()
        self.asistencias_view = AsistenciasWindow()

        self.stack.addWidget(self.dashboard_view)
        self.stack.addWidget(self.registro_view)
        self.stack.addWidget(self.reportes_view)
        self.stack.addWidget(self.mensuales_view)
        self.stack.addWidget(self.config_view)
        self.stack.addWidget(self.tarifas_view)
        self.stack.addWidget(self.edicion_view)
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
            self.btn_edicion.clicked.connect(self.mostrar_edicion)
            self.btn_usuarios.clicked.connect(self.mostrar_usuarios)
            self.btn_asistencias.clicked.connect(self.mostrar_asistencias)

        self.btn_cerrar_sesion.clicked.connect(self.cerrar_sesion)

        layout_principal.addWidget(self.sidebar)
        layout_principal.addWidget(contenedor, 1)

        self.mostrar_dashboard()
        self.aplicar_estado_sidebar()

    # =========================================================
    # SIDEBAR
    # =========================================================
    def toggle_sidebar(self):
        self.sidebar_expandido = not self.sidebar_expandido
        self.aplicar_estado_sidebar()

    def aplicar_estado_sidebar(self):
        icono_menu = self.cargar_icono("menu.svg")
        self.btn_toggle_sidebar.setIcon(icono_menu)
        self.btn_toggle_sidebar.setIconSize(QSize(18, 18))
        self.btn_toggle_sidebar.setText("")

        if self.sidebar_expandido:
            self.sidebar.setMinimumWidth(self.SIDEBAR_EXPANDED_WIDTH)
            self.sidebar.setMaximumWidth(self.SIDEBAR_EXPANDED_WIDTH)

            self.titulo_sidebar.show()
            self.subtitulo_sidebar.show()

            for btn, texto, icono in self.sidebar_buttons_data:
                btn.setText(texto)
                btn.setIcon(self.cargar_icono(icono))
                btn.setIconSize(self.ICON_SIZE)
                btn.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        padding-left: 12px;
                        font-size: 14px;
                    }
                """)

            self.btn_cerrar_sesion.setText("Cerrar sesión")
            self.btn_cerrar_sesion.setIcon(self.cargar_icono("salir.svg"))
            self.btn_cerrar_sesion.setIconSize(self.ICON_SIZE)

        else:
            self.sidebar.setMinimumWidth(self.SIDEBAR_COLLAPSED_WIDTH)
            self.sidebar.setMaximumWidth(self.SIDEBAR_COLLAPSED_WIDTH)

            self.titulo_sidebar.hide()
            self.subtitulo_sidebar.hide()

            for btn, _texto, icono in self.sidebar_buttons_data:
                btn.setText("")
                btn.setIcon(self.cargar_icono(icono))
                btn.setIconSize(self.ICON_SIZE)
                btn.setStyleSheet("""
                    QPushButton {
                        text-align: center;
                        padding-left: 4px;
                        padding-right: 4px;
                        font-size: 11px;
                    }
                """)

            self.btn_cerrar_sesion.setText("")
            self.btn_cerrar_sesion.setIcon(self.cargar_icono("salir.svg"))
            self.btn_cerrar_sesion.setIconSize(self.ICON_SIZE)

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

    def mostrar_edicion(self):
        self.label_modulo.setText("Edición de ingresos")
        self.edicion_view.cargar_datos()
        self.stack.setCurrentWidget(self.edicion_view)

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
        resumen = registrar_asistencia_salida(self.usuario)

        QMessageBox.information(
            self,
            "Resumen del día",
            f"Sesión: {resumen['hora_inicio'].strftime('%d-%m-%Y %H:%M') if resumen['hora_inicio'] else 'N/A'} - ahora\n"
            f"Vehículos cobrados: {resumen['cantidad']}\n"
            f"Total recaudado: ${resumen['total']:.0f}"
        )
        self.close()