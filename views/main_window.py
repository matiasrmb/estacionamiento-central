from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout,
    QHBoxLayout, QMessageBox, QStackedWidget,
    QSizePolicy, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, QTimer

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
from datetime import datetime, timedelta


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

        self.timer_operativo = QTimer(self)
        self.timer_operativo.timeout.connect(self.actualizar_panel_operativo)
        self.timer_operativo.start(5000)
        self.actualizar_panel_operativo()

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
        self.btn_edicion = QPushButton("✏️ Edición de ingresos")
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
                self.btn_edicion,
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

        # =========================================================
        # PANEL OPERATIVO
        # =========================================================
        self.panel_operativo = QFrame()
        self.panel_operativo.setObjectName("PanelOperativo")

        panel_layout = QVBoxLayout(self.panel_operativo)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(8)

        titulo_panel = QLabel("Estado del sistema")
        titulo_panel.setObjectName("TituloPanelOperativo")
        panel_layout.addWidget(titulo_panel)

        self.label_estado_turno = QLabel("Turno en operación")
        self.label_estado_turno.setObjectName("EstadoOperativoOk")

        self.label_estado_subida = QLabel("Subida temporal: no activa")
        self.label_estado_subida.setObjectName("EstadoOperativoNeutro")

        self.label_estado_activos = QLabel("Vehículos activos: 0")
        self.label_estado_activos.setObjectName("EstadoOperativoNeutro")

        panel_layout.addWidget(self.label_estado_turno)
        panel_layout.addWidget(self.label_estado_subida)
        panel_layout.addWidget(self.label_estado_activos)

        sidebar_layout.addSpacing(8)
        sidebar_layout.addWidget(self.panel_operativo)

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

        layout_principal.addWidget(sidebar)
        layout_principal.addWidget(contenedor)

        self.mostrar_dashboard()

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

    def normalizar_hora_sidebar(self, valor):
        """
        Convierte distintos formatos de hora a objeto time.
        """
        if hasattr(valor, "hour") and hasattr(valor, "minute"):
            return valor

        valor_str = str(valor).strip()

        try:
            return datetime.strptime(valor_str, "%H:%M:%S").time()
        except ValueError:
            return datetime.strptime(valor_str, "%H:%M").time()


    def subida_vigente_sidebar(self):
        """
        Determina si existe una subida temporal activa en este momento.
        """
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
        """
        Refresca indicadores rápidos del sidebar.
        """
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