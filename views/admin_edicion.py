from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHBoxLayout,
    QMessageBox, QGroupBox
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
    Ventana para administradores: permite editar ingresos especiales.
    - Eliminar ingresos en espera (con respaldo).
    - Revertir ingresos en espera a estado activo.
    - Reingresar ingresos cerrados manteniendo hora y tarifa.
    """
    def __init__(self, usuario_admin):
        super().__init__()
        self.usuario_admin = usuario_admin
        self.setWindowTitle("Panel de Edición Manual de Ingresos")
        self.setMinimumSize(750, 460)
        resize_width = 900
        resize_height = 560
        self.resize(resize_width, resize_height)
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Título
        titulo = QLabel("✏️ Edición Manual de Ingresos")
        titulo.setObjectName("TituloVentana")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        # Descripción
        descripcion = QLabel("Ingresos marcados como 'EN ESPERA' o 'CERRADO reciente'.")
        descripcion.setAlignment(Qt.AlignCenter)
        layout.addWidget(descripcion)

        # Tabla dentro de un grupo
        grupo_tabla = QGroupBox("Ingresos disponibles para edición")
        layout_tabla = QVBoxLayout()
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["ID", "Patente", "Hora ingreso", "Estado"])
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.verticalHeader().setDefaultSectionSize(34)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        layout_tabla.addWidget(self.tabla)
        grupo_tabla.setLayout(layout_tabla)
        layout.addWidget(grupo_tabla)

        # Botones de acción
        botones_layout = QHBoxLayout()

        self.btn_revertir = QPushButton("Revertir ingreso en espera")
        self.btn_revertir.clicked.connect(self.revertir_en_espera)
        self.btn_revertir.setMinimumHeight(40)
        botones_layout.addWidget(self.btn_revertir)

        self.btn_reingresar = QPushButton("Reingresar vehículo cerrado")
        self.btn_reingresar.clicked.connect(self.reingresar)
        self.btn_reingresar.setMinimumHeight(40)
        botones_layout.addWidget(self.btn_reingresar)

        self.btn_eliminar = QPushButton("Eliminar ingreso en espera")
        self.btn_eliminar.setObjectName("BotonPeligro")
        self.btn_eliminar.clicked.connect(self.eliminar_ingreso)
        self.btn_eliminar.setMinimumHeight(40)
        botones_layout.addWidget(self.btn_eliminar)

        layout.addLayout(botones_layout)
        self.setLayout(layout)

    def cargar_datos(self):
        self.tabla.setRowCount(0)
        ingresos = obtener_ingresos_editables()

        for fila, ingreso in enumerate(ingresos):
            self.tabla.insertRow(fila)
            self.tabla.setItem(fila, 0, QTableWidgetItem(str(ingreso["id_ingreso"])))
            self.tabla.setItem(fila, 1, QTableWidgetItem(ingreso["patente"]))
            self.tabla.setItem(
                fila, 2,
                QTableWidgetItem(ingreso["fecha_hora_ingreso"].strftime("%d-%m-%Y %H:%M:%S"))
            )
            self.tabla.setItem(fila, 3, QTableWidgetItem(ingreso["estado"]))

    def revertir_en_espera(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Selecciona", "Selecciona una fila primero.")
            return

        estado = self.tabla.item(fila, 3).text()
        if estado != "EN ESPERA":
            QMessageBox.warning(self, "No válido", "Solo puedes revertir ingresos marcados como 'EN ESPERA'.")
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
            QMessageBox.warning(self, "No válido", "Solo puedes reingresar vehículos cerrados.")
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
            QMessageBox.warning(self, "No válido", "Solo puedes eliminar ingresos 'en espera'.")
            return

        id_ingreso = int(self.tabla.item(fila, 0).text())
        patente = self.tabla.item(fila, 1).text()

        confirmacion = QMessageBox.question(
            self, "Eliminar ingreso",
            f"¿Eliminar ingreso en espera de {patente}? Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirmacion == QMessageBox.Yes:
            eliminar_ingreso_con_respaldo(id_ingreso, self.usuario_admin)
            QMessageBox.information(self, "Eliminado", "Ingreso eliminado correctamente.")
            self.cargar_datos()
