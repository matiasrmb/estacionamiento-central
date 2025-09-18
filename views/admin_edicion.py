from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHBoxLayout,
    QMessageBox
)
from controllers.registro_controller import obtener_ingresos_en_espera, eliminar_ingreso_con_respaldo


class EdicionIngresosWindow(QWidget):
    """
    Ventana exclusiva para administradores que permite eliminar manualmente registros de ingresos
    marcados como 'en espera'. Al eliminar, se guarda automáticamente un respaldo en la tabla 
    'ingresos_eliminados' para auditoría.
    """
    def __init__(self, usuario_admin):
        super().__init__()
        self.usuario_admin = usuario_admin
        self.setWindowTitle("Panel de Edición Manual de Ingresos")
        self.setFixedSize(700, 400)
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.label = QLabel("Ingresos marcados como 'en espera'")
        layout.addWidget(self.label)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["ID Ingreso", "Patente", "Hora de Ingreso"])
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.tabla)

        # Botón para eliminar seleccionado
        boton_layout = QHBoxLayout()
        self.btn_eliminar = QPushButton("Eliminar ingreso seleccionado")
        self.btn_eliminar.clicked.connect(self.eliminar_ingreso)
        boton_layout.addStretch()
        boton_layout.addWidget(self.btn_eliminar)
        layout.addLayout(boton_layout)

        self.setLayout(layout)

    def cargar_datos(self):
        self.tabla.setRowCount(0)
        ingresos = obtener_ingresos_en_espera()

        for fila, ingreso in enumerate(ingresos):
            self.tabla.insertRow(fila)
            self.tabla.setItem(fila, 0, QTableWidgetItem(str(ingreso["id_ingreso"])))
            self.tabla.setItem(fila, 1, QTableWidgetItem(ingreso["patente"]))
            self.tabla.setItem(fila, 2, QTableWidgetItem(ingreso["fecha_hora_ingreso"].strftime("%d-%m-%Y %H:%M")))

    def eliminar_ingreso(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Atención", "Selecciona un ingreso para eliminar.")
            return

        id_ingreso = int(self.tabla.item(fila, 0).text())
        patente = self.tabla.item(fila, 1).text()

        confirmacion = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Seguro que deseas eliminar el ingreso de {patente}?\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirmacion == QMessageBox.Yes:
            eliminar_ingreso_con_respaldo(id_ingreso, self.usuario_admin)
            QMessageBox.information(self, "Ingreso eliminado", "Ingreso eliminado correctamente.")
            self.cargar_datos()
