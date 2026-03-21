from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHBoxLayout,
    QMessageBox, QGroupBox, QHeaderView
)
from PySide6.QtCore import Qt


from controllers.registro_controller import (
    obtener_ingresos_editables,
    eliminar_ingreso_con_respaldo,
    revertir_en_espera,
    reingresar_vehiculo_cerrado
)


class EdicionIngresosWindow(QWidget):
    """
    Vista administrativa para editar ingresos especiales.

    Permite:
    - Revertir ingresos en espera.
    - Reingresar vehículos cerrados recientemente.
    - Eliminar ingresos en espera con respaldo.
    """

    def __init__(self, usuario_admin, on_volver_panel=None):
        super().__init__()
        self.usuario_admin = usuario_admin
        self.on_volver_panel = on_volver_panel
        self.setMinimumSize(1000, 650)
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # =========================================================
        # ENCABEZADO
        # =========================================================
        header_layout = QHBoxLayout()

        self.btn_volver = QPushButton("Volver al panel principal")
        self.btn_volver.setObjectName("BotonSecundario")
        self.btn_volver.setMinimumHeight(38)
        self.btn_volver.clicked.connect(self.volver_al_panel)

        titulo = QLabel("Edición manual de ingresos")
        titulo.setObjectName("TituloVentana")
        titulo.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(self.btn_volver, alignment=Qt.AlignLeft)
        header_layout.addStretch()
        header_layout.addWidget(titulo)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        descripcion = QLabel(
            "Aquí puedes gestionar ingresos marcados como 'EN ESPERA' o "
            "'CERRADO' reciente para corregir situaciones operativas."
        )
        descripcion.setObjectName("SubtituloSeccion")
        descripcion.setWordWrap(True)
        layout.addWidget(descripcion)

        # =========================================================
        # TABLA
        # =========================================================
        grupo_tabla = QGroupBox("Ingresos disponibles para edición")
        layout_tabla = QVBoxLayout()
        layout_tabla.setContentsMargins(12, 18, 12, 18)
        layout_tabla.setSpacing(10)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["ID", "Patente", "Hora ingreso", "Estado"])
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setDefaultSectionSize(36)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

        layout_tabla.addWidget(self.tabla)
        grupo_tabla.setLayout(layout_tabla)
        layout.addWidget(grupo_tabla)

        # =========================================================
        # ACCIONES
        # =========================================================
        grupo_acciones = QGroupBox("Acciones disponibles")
        layout_acciones = QHBoxLayout()
        layout_acciones.setContentsMargins(12, 18, 12, 18)
        layout_acciones.setSpacing(10)

        self.btn_revertir = QPushButton("Revertir ingreso en espera")
        self.btn_revertir.setMinimumHeight(40)
        self.btn_revertir.clicked.connect(self.revertir_en_espera)

        self.btn_reingresar = QPushButton("Reingresar vehículo cerrado")
        self.btn_reingresar.setMinimumHeight(40)
        self.btn_reingresar.clicked.connect(self.reingresar)

        self.btn_eliminar = QPushButton("Eliminar ingreso en espera")
        self.btn_eliminar.setObjectName("BotonPeligro")
        self.btn_eliminar.setMinimumHeight(40)
        self.btn_eliminar.clicked.connect(self.eliminar_ingreso)

        self.btn_refrescar = QPushButton("Actualizar lista")
        self.btn_refrescar.setObjectName("BotonSecundario")
        self.btn_refrescar.setMinimumHeight(40)
        self.btn_refrescar.clicked.connect(self.cargar_datos)

        layout_acciones.addWidget(self.btn_revertir)
        layout_acciones.addWidget(self.btn_reingresar)
        layout_acciones.addWidget(self.btn_eliminar)
        layout_acciones.addWidget(self.btn_refrescar)

        grupo_acciones.setLayout(layout_acciones)
        layout.addWidget(grupo_acciones)

        self.setLayout(layout)

    def volver_al_panel(self):
        if callable(self.on_volver_panel):
            self.on_volver_panel()

    def cargar_datos(self):
        self.tabla.setRowCount(0)
        ingresos = obtener_ingresos_editables()

        for fila, ingreso in enumerate(ingresos):
            self.tabla.insertRow(fila)

            item_id = QTableWidgetItem(str(ingreso["id_ingreso"]))
            item_patente = QTableWidgetItem(ingreso["patente"])
            item_fecha = QTableWidgetItem(
                ingreso["fecha_hora_ingreso"].strftime("%d-%m-%Y %H:%M:%S")
            )
            item_estado = QTableWidgetItem(ingreso["estado"])

            item_id.setTextAlignment(Qt.AlignCenter)
            item_patente.setTextAlignment(Qt.AlignCenter)
            item_estado.setTextAlignment(Qt.AlignCenter)

            for item in (item_id, item_patente, item_fecha, item_estado):
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)

            self.tabla.setItem(fila, 0, item_id)
            self.tabla.setItem(fila, 1, item_patente)
            self.tabla.setItem(fila, 2, item_fecha)
            self.tabla.setItem(fila, 3, item_estado)

    def revertir_en_espera(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Selecciona", "Selecciona una fila primero.")
            return

        estado = self.tabla.item(fila, 3).text()
        if estado != "EN ESPERA":
            QMessageBox.warning(
                self,
                "No válido",
                "Solo puedes revertir ingresos marcados como 'EN ESPERA'."
            )
            return

        id_ingreso = int(self.tabla.item(fila, 0).text())
        if revertir_en_espera(id_ingreso):
            QMessageBox.information(self, "Éxito", "Ingreso revertido correctamente.")
            self.cargar_datos()
        else:
            QMessageBox.critical(self, "Error", "No se pudo revertir el ingreso.")

    def reingresar(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Selecciona", "Selecciona una fila primero.")
            return

        estado = self.tabla.item(fila, 3).text()
        if estado != "CERRADO":
            QMessageBox.warning(
                self,
                "No válido",
                "Solo puedes reingresar vehículos cerrados."
            )
            return

        id_ingreso = int(self.tabla.item(fila, 0).text())
        if reingresar_vehiculo_cerrado(id_ingreso):
            QMessageBox.information(self, "Éxito", "Vehículo reingresado correctamente.")
            self.cargar_datos()
        else:
            QMessageBox.critical(self, "Error", "No se pudo reingresar el vehículo.")

    def eliminar_ingreso(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Selecciona", "Selecciona una fila primero.")
            return

        estado = self.tabla.item(fila, 3).text()
        if estado != "EN ESPERA":
            QMessageBox.warning(
                self,
                "No válido",
                "Solo puedes eliminar ingresos 'en espera'."
            )
            return

        id_ingreso = int(self.tabla.item(fila, 0).text())
        patente = self.tabla.item(fila, 1).text()

        confirmacion = QMessageBox.question(
            self,
            "Eliminar ingreso",
            f"¿Eliminar ingreso en espera de {patente}? Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirmacion == QMessageBox.Yes:
            eliminar_ingreso_con_respaldo(id_ingreso, self.usuario_admin)
            QMessageBox.information(self, "Eliminado", "Ingreso eliminado correctamente.")
            self.cargar_datos()