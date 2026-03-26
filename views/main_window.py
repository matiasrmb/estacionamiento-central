from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout,
    QHBoxLayout, QMessageBox, QStackedWidget,
    QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, QTimer, QSize
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
from controllers.subida_controller import obtener_subida_activa
from controllers.registro_controller import obtener_vehiculos_activos


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

        self.timer_operativo = QTimer(self)
        self.timer_operativo.timeout.connect(self.actualizar_panel_operativo)
        self.timer_operativo.start(5000)
        self.actualizar_panel_operativo()

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
        header_sidebar.addWidget(self.btn_toggle_sidebar, 0, alignment=Qt.AlignRight)

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

        # =========================================================
        # PANEL OPERATIVO
        # =========================================================
        self.panel_operativo = QFrame()
        self.panel_operativo.setObjectName("PanelOperativo")

        panel_layout = QVBoxLayout(self.panel_operativo)
        panel_layout.setContentsMargins(8, 6, 8, 6)
        panel_layout.setSpacing(6)

        self.titulo_panel_operativo = QLabel("Estado del sistema")
        self.titulo_panel_operativo.setObjectName("TituloPanelOperativo")
        panel_layout.addWidget(self.titulo_panel_operativo)

        self.label_estado_turno = QLabel("Turno en operación")
        self.label_estado_turno.setObjectName("EstadoOperativoOk")
        self.label_estado_turno.setWordWrap(True)

        self.label_estado_subida = QLabel("Subida temporal: no activa")
        self.label_estado_subida.setObjectName("EstadoOperativoNeutro")
        self.label_estado_subida.setWordWrap(True)

        self.label_estado_activos = QLabel("Vehículos activos: 0")
        self.label_estado_activos.setObjectName("EstadoOperativoNeutro")
        self.label_estado_activos.setWordWrap(True)

        panel_layout.addWidget(self.label_estado_turno)
        panel_layout.addWidget(self.label_estado_subida)
        panel_layout.addWidget(self.label_estado_activos)

        sidebar_layout.addSpacing(4)
        sidebar_layout.addWidget(self.panel_operativo)

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
            self.panel_operativo.show()
            self.titulo_panel_operativo.show()

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
            self.panel_operativo.hide()

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
        self.actualizar_panel_operativo()

    def mostrar_registro(self):
        self.label_modulo.setText("Registro de vehículos")
        self.stack.setCurrentWidget(self.registro_view)
        self.actualizar_panel_operativo()

    def mostrar_reportes(self):
        self.label_modulo.setText("Reportes")
        self.stack.setCurrentWidget(self.reportes_view)
        self.actualizar_panel_operativo()

    def mostrar_mensuales(self):
        self.label_modulo.setText("Clientes mensuales")
        self.stack.setCurrentWidget(self.mensuales_view)
        self.actualizar_panel_operativo()

    def mostrar_configuracion(self):
        self.label_modulo.setText("Configuración")
        self.stack.setCurrentWidget(self.config_view)
        self.actualizar_panel_operativo()

    def mostrar_tarifas(self):
        self.label_modulo.setText("Tarifas personalizadas")
        self.stack.setCurrentWidget(self.tarifas_view)
        self.actualizar_panel_operativo()

    def mostrar_edicion(self):
        self.label_modulo.setText("Edición de ingresos")
        self.edicion_view.cargar_datos()
        self.stack.setCurrentWidget(self.edicion_view)
        self.actualizar_panel_operativo()

    def mostrar_usuarios(self):
        self.label_modulo.setText("Gestión de usuarios")
        self.stack.setCurrentWidget(self.usuarios_view)
        self.actualizar_panel_operativo()

    def mostrar_asistencias(self):
        self.label_modulo.setText("Asistencias")
        self.stack.setCurrentWidget(self.asistencias_view)
        self.actualizar_panel_operativo()

    # =========================================================
    # PANEL OPERATIVO
    # =========================================================
    def normalizar_hora_sidebar(self, valor):
        if hasattr(valor, "hour") and hasattr(valor, "minute"):
            return valor

        valor_str = str(valor).strip()

        try:
            return datetime.strptime(valor_str, "%H:%M:%S").time()
        except ValueError:
            return datetime.strptime(valor_str, "%H:%M").time()

    def subida_vigente_sidebar(self):
        subida = obtener_subida_activa()
        if not subida:
            return False, None

        try:
            ahora = datetime.now()

            hora_inicio_time = self.normalizar_hora_sidebar(subida["hora_inicio"])
            hora_fin_time = self.normalizar_hora_sidebar(subida["hora_fin"])

            hora_inicio = datetime.combine(ahora.date(), hora_inicio_time)
            hora_fin = datetime.combine(ahora.date(), hora_fin_time)

            if hora_fin > hora_inicio:
                vigente = hora_inicio <= ahora <= hora_fin
            else:
                vigente = ahora >= hora_inicio or ahora.time() <= hora_fin_time

            return vigente, subida

        except Exception as e:
            print(f"[WARN] No se pudo evaluar subida en sidebar: {e}")
            return False, subida

    def actualizar_panel_operativo(self):
        try:
            self.label_estado_turno.setText("Turno en operación")
            self.label_estado_turno.setObjectName("EstadoOperativoOk")

            activos = obtener_vehiculos_activos()
            cantidad_activos = len(activos)
            self.label_estado_activos.setText(f"Vehículos activos: {cantidad_activos}")

            if cantidad_activos > 0:
                self.label_estado_activos.setObjectName("EstadoOperativoWarn")
            else:
                self.label_estado_activos.setObjectName("EstadoOperativoNeutro")

            vigente, subida = self.subida_vigente_sidebar()

            if vigente and subida:
                monto = subida.get("monto_adicional", 0)
                h_ini = self.normalizar_hora_sidebar(subida["hora_inicio"]).strftime("%H:%M")
                h_fin = self.normalizar_hora_sidebar(subida["hora_fin"]).strftime("%H:%M")
                self.label_estado_subida.setText(f"Subida activa: +${monto} ({h_ini}-{h_fin})")
                self.label_estado_subida.setObjectName("EstadoOperativoWarn")
            elif subida:
                monto = subida.get("monto_adicional", 0)
                h_ini = self.normalizar_hora_sidebar(subida["hora_inicio"]).strftime("%H:%M")
                h_fin = self.normalizar_hora_sidebar(subida["hora_fin"]).strftime("%H:%M")
                self.label_estado_subida.setText(f"Subida configurada: +${monto} ({h_ini}-{h_fin})")
                self.label_estado_subida.setObjectName("EstadoOperativoNeutro")
            else:
                self.label_estado_subida.setText("Subida temporal: no activa")
                self.label_estado_subida.setObjectName("EstadoOperativoNeutro")

            for label in (
                self.label_estado_turno,
                self.label_estado_activos,
                self.label_estado_subida
            ):
                label.style().unpolish(label)
                label.style().polish(label)
                label.update()

        except Exception as e:
            print(f"[WARN] No se pudo actualizar panel operativo: {e}")

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