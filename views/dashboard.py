from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QMessageBox,
    QGridLayout, QHBoxLayout
)
from PySide6.QtCore import QDateTime, QTimer, Qt

from controllers.dashboard_controller import obtener_resumen_diario
from controllers.cierres_controller import realizar_cierre_diario
from utils.db import db_cursor
from utils.local_preferences import obtener_modo_privacidad_metricas
from views.registro import TarjetaResumen
from datetime import datetime


DASHBOARD_METRICAS = (
    ("Operación", (
        ("ingresos", "Ingresos registrados", "0", "ingresos-registrados.svg", "Ingresos creados desde el último cierre."),
        ("vehiculos", "Vehículos activos", "0", "vehiculos-activos.svg", "Vehículos con estadía abierta. No incluye lavados solos."),
        ("banos", "Usos de baño", "0 | $0", "usos-bano-hoy.svg", "Usos y cobros pendientes de cierre."),
        ("lavados", "Lavados cobrados", "0 | $0", "lavados-cobrados.svg", "Solo lavados finalizados y cobrados, pendientes de cierre. Los lavados asociados a una estadía se cobran dentro de la salida del vehículo."),
        ("mensualidades", "Mensualidades del mes", "0 | $0", "mensualidades-mes.svg", "Pagos registrados en el mes calendario actual; puede incluir pagos ya cerrados."),
        ("noches", "Noches cobradas", "0 | $0", "noches-cobradas.svg", "Cobros prepagados de Noche pendientes de cierre."),
    )),
    ("Caja", (
        ("total_turno", "Total turno", "$0", "total-turno.svg", "Cobros pendientes de cierre."),
        ("gastos", "Gastos", "$0", "gastos.svg", "Gastos operacionales pendientes de cierre."),
        ("neto_caja", "Neto en caja", "$0", "neto-caja.svg", "Total turno menos gastos pendientes de cierre."),
    )),
    ("Proyección", (
        ("estimado", "Estimado por cobrar", "$0", "estimado-activos.svg", "Cotización actual de estadías abiertas y servicios aún no cobrados. No es efectivo en caja."),
        ("total_proyectado", "Total proyectado", "$0", "total-proyectado.svg", "Recaudado pendiente de cierre más cobros estimados aún no realizados. No descuenta gastos."),
    )),
)


class DashboardWindow(QWidget):
    """
    Vista de resumen diario del estacionamiento.
    Muestra estadísticas del turno actual y permite realizar el cierre diario.
    """

    def __init__(self, usuario, rol, api_token=None, api_warning=None, on_ir_panel=None, on_ir_registro=None, on_ir_reportes=None):
        super().__init__()
        self.usuario = usuario
        self.rol = rol
        self.api_token = api_token
        self.api_warning = api_warning
        self.on_ir_panel = on_ir_panel
        self.on_ir_registro = on_ir_registro
        self.on_ir_reportes = on_ir_reportes
        self.modo_privacidad_metricas = obtener_modo_privacidad_metricas()

        self.actualizacion_habilitada = True
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # =========================================================
        # ENCABEZADO
        # =========================================================

        self.label_periodo = QLabel(self.obtener_periodo_resumen())
        self.label_periodo.setObjectName("SubtituloSeccion")
        self.label_periodo.setAlignment(Qt.AlignLeft)
        self.label_periodo.setWordWrap(True)
        layout.addWidget(self.label_periodo)

        self.label_hora = QLabel()
        self.label_hora.setAlignment(Qt.AlignLeft)
        self.label_hora.setWordWrap(True)
        layout.addWidget(self.label_hora)

        self.label_usuario = QLabel(f"Usuario activo: {self.usuario} ({self.rol})")
        self.label_usuario.setAlignment(Qt.AlignLeft)
        self.label_usuario.setWordWrap(True)
        layout.addWidget(self.label_usuario)

        # =========================================================
        # TARJETAS DE RESUMEN
        # =========================================================
        self.tarjetas_metricas = {}
        for seccion, definiciones in DASHBOARD_METRICAS:
            titulo_seccion = QLabel(seccion)
            titulo_seccion.setObjectName("SubtituloSeccion")
            layout.addWidget(titulo_seccion)

            grid_resumen = QGridLayout()
            grid_resumen.setHorizontalSpacing(12)
            grid_resumen.setVerticalSpacing(12)
            for indice, (clave, titulo, valor, icono, ayuda) in enumerate(definiciones):
                tarjeta = TarjetaResumen(
                    titulo,
                    valor,
                    icono,
                    ayuda,
                    modo_privacidad=self.modo_privacidad_metricas,
                )
                self.tarjetas_metricas[clave] = tarjeta
                grid_resumen.addWidget(tarjeta, indice // 3, indice % 3)
            for columna in range(3):
                grid_resumen.setColumnStretch(columna, 1)
            layout.addLayout(grid_resumen)

        # =========================================================
        # ACCIONES PRINCIPALES
        # =========================================================
        acciones_layout = QHBoxLayout()
        acciones_layout.setSpacing(10)

        self.boton_cierre = QPushButton("Realizar cierre diario")
        self.boton_cierre.setMinimumHeight(42)
        self.boton_cierre.clicked.connect(self.confirmar_cierre_diario)

        acciones_layout.addWidget(self.boton_cierre)
        acciones_layout.addStretch()

        layout.addLayout(acciones_layout)

        # =========================================================
        # ACCESOS RÁPIDOS
        # =========================================================
        accesos_titulo = QLabel("Accesos rápidos")
        accesos_titulo.setObjectName("SubtituloSeccion")
        accesos_titulo.setAlignment(Qt.AlignLeft)
        layout.addWidget(accesos_titulo)

        accesos_layout = QHBoxLayout()
        accesos_layout.setSpacing(10)

        self.btn_ir_registro = QPushButton("Ir a registro")
        self.btn_ir_registro.setMinimumHeight(40)
        self.btn_ir_registro.clicked.connect(self.ir_a_registro)
        accesos_layout.addWidget(self.btn_ir_registro)

        if self.rol == "administrador":
            self.btn_ir_reportes = QPushButton("Ir a reportes")
            self.btn_ir_reportes.setMinimumHeight(40)
            self.btn_ir_reportes.clicked.connect(self.ir_a_reportes)
            accesos_layout.addWidget(self.btn_ir_reportes)

        accesos_layout.addStretch()
        layout.addLayout(accesos_layout)

        layout.addStretch()
        self.setLayout(layout)

        # Timers
        self.timer = QTimer()
        self.timer.timeout.connect(self.actualizar_hora)
        self.timer.start(1000)
        self.actualizar_hora()

        self.timer_resumen = QTimer()
        self.timer_resumen.timeout.connect(self.actualizar_resumen)
        self.timer_resumen.start(1000)

        self.actualizar_resumen()

    def actualizar_hora(self):
        hora_actual = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.label_hora.setText(f"Hora actual: {hora_actual}")

    def obtener_periodo_resumen(self):
        with db_cursor(dictionary=True) as cursor:
            cursor.execute("SELECT MAX(fecha_cierre) AS ultima_cierre FROM cierres_diarios")
            row = cursor.fetchone()

        if row and row["ultima_cierre"]:
            fecha_inicio = row["ultima_cierre"].strftime("%d/%m/%Y %H:%M")
        else:
            fecha_inicio = "Inicio del sistema"

        fecha_fin = datetime.now().strftime("%d/%m/%Y %H:%M")
        return f"Período del turno: {fecha_inicio} → {fecha_fin}"

    def actualizar_resumen(self):
        if not self.actualizacion_habilitada:
            return

        resumen = obtener_resumen_diario()
        self.tarjetas_metricas["ingresos"].set_valor(str(resumen["total_ingresos"]))
        self.tarjetas_metricas["vehiculos"].set_valor(str(resumen["vehiculos_activos"]))
        self.tarjetas_metricas["banos"].set_valor(
            f"{resumen['usos_bano']} | ${resumen['usos_bano_monto']:.0f}"
        )
        self.tarjetas_metricas["lavados"].set_valor(
            f"{resumen['lavados_cobrados']} | ${resumen['lavados_cobrados_monto']:.0f}"
        )
        self.tarjetas_metricas["mensualidades"].set_valor(
            f"{resumen['mensualidades_mes']} | ${resumen['mensualidades_mes_monto']:.0f}"
        )
        self.tarjetas_metricas["noches"].set_valor(
            f"{resumen['noches_cobradas']} | ${resumen['noches_cobradas_monto']:.0f}"
        )
        self.tarjetas_metricas["total_turno"].set_valor(f"${resumen['total_turno']:.0f}")
        self.tarjetas_metricas["gastos"].set_valor(f"${resumen['gastos']:.0f}")
        self.tarjetas_metricas["neto_caja"].set_valor(f"${resumen['neto_caja']:.0f}")
        self.tarjetas_metricas["estimado"].set_valor(f"${resumen['estimado_por_cobrar']:.0f}")
        self.tarjetas_metricas["total_proyectado"].set_valor(f"${resumen['total_proyectado']:.0f}")

        self.label_periodo.setText(self.obtener_periodo_resumen())

        if resumen["total_ingresos"] > 0 or resumen["usos_bano"] > 0 or resumen["total_turno"] > 0:
            self.actualizacion_habilitada = True

    def confirmar_cierre_diario(self):
        respuesta = QMessageBox.question(
            self,
            "Confirmar cierre diario",
            "¿Estás seguro de que deseas realizar el cierre diario?\nEsto marcará como cerradas todas las salidas registradas hasta ahora.",
            QMessageBox.Yes | QMessageBox.No
        )
        if respuesta == QMessageBox.Yes:
            exito, mensaje = realizar_cierre_diario(self.api_token, self.api_warning)
            if exito:
                QMessageBox.information(self, "Éxito", mensaje)

                # Algunas métricas no dependen del cierre; recargar evita mostrarlas como cero.
                self.actualizacion_habilitada = True
                self.actualizar_resumen()
            else:
                QMessageBox.information(self, "Cierre diario", mensaje)

    def ir_a_registro(self):
        if callable(self.on_ir_registro):
            self.on_ir_registro()

    def ir_a_reportes(self):
        if callable(self.on_ir_reportes):
            self.on_ir_reportes()
