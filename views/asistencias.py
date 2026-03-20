from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, 
    QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QDateEdit, QMessageBox
)
from PySide6.QtCore import QDate, Qt

from controllers.asistencias_controller import obtener_asistencias
from utils.pdf_asistencias import exportar_asistencias_pdf

class AsistenciasWindow(QWidget):
    """
    Ventana que permite visualizar y exportar asistencias de usuarios, 
    filtradas por fecha y nombre de usuario.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registro de Asistencias")
        self.setMinimumSize(900, 600) 
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        titulo = QLabel("🕒 Registro de asistencias")
        titulo.setObjectName("TituloVentana")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        # Filtros
        filtro_layout = QHBoxLayout()
        filtro_layout.setSpacing(10)

        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Usuario")
        self.input_usuario.setMinimumWidth(100)

        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setCalendarPopup(True)
        self.fecha_inicio.setDate(QDate.currentDate())

        self.fecha_fin = QDateEdit()
        self.fecha_fin.setCalendarPopup(True)
        self.fecha_fin.setDate(QDate.currentDate())

        self.btn_filtrar = QPushButton("Buscar")
        self.btn_filtrar.setMinimumHeight(30)
        self.btn_filtrar.clicked.connect(self.filtrar)
        self.btn_filtrar.setMinimumHeight(38)

        self.btn_exportar = QPushButton("Exportar PDF")
        self.btn_exportar.setMinimumHeight(30)
        self.btn_exportar.clicked.connect(self.exportar_pdf)
        self.btn_exportar.setMinimumHeight(38)

        filtro_layout.addWidget(QLabel("Usuario:"))
        filtro_layout.addWidget(self.input_usuario)
        filtro_layout.addWidget(QLabel("Desde:"))
        filtro_layout.addWidget(self.fecha_inicio)
        filtro_layout.addWidget(QLabel("Hasta:"))
        filtro_layout.addWidget(self.fecha_fin)
        filtro_layout.addWidget(self.btn_filtrar)
        filtro_layout.addWidget(self.btn_exportar)

        layout.addLayout(filtro_layout)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels([
            "Usuario", "Hora de Inicio", "Hora de Salida", "Movimientos", "Total Recaudado"
        ])
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.verticalHeader().setDefaultSectionSize(34)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tabla)

        self.setLayout(layout)

    def filtrar(self):
        """Ejecuta la búsqueda de asistencias según los filtros ingresados."""
        try:
            usuario = self.input_usuario.text().strip()
            fecha_inicio = self.fecha_inicio.date().toPython()
            fecha_fin = self.fecha_fin.date().toPython()

            datos = obtener_asistencias(usuario or None, fecha_inicio, fecha_fin)
            self.resultados = datos  

            self.tabla.setRowCount(len(datos))

            for i, fila in enumerate(datos):
                self.tabla.setItem(i, 0, QTableWidgetItem(fila["usuario"]))
                self.tabla.setItem(i, 1, QTableWidgetItem(str(fila["hora_inicio"])))
                self.tabla.setItem(i, 2, QTableWidgetItem(str(fila["hora_salida"] or "Activo")))
                self.tabla.setItem(i, 3, QTableWidgetItem(str(fila["cantidad_movimientos"])))
                self.tabla.setItem(i, 4, QTableWidgetItem(f"${fila['total_recaudado']:.0f}"))

            if not datos:
                QMessageBox.information(self, "Sin resultados", "No se encontraron asistencias con esos filtros.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error:\n{e}")

    def exportar_pdf(self):
        """Exporta los resultados actuales de la tabla a un archivo PDF."""
        try:
            if hasattr(self, "resultados") and self.resultados:
                exportar_asistencias_pdf(self.resultados)
            else:
                QMessageBox.warning(self, "Sin datos", "Primero realiza una búsqueda con resultados.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar el PDF:\n{e}")
