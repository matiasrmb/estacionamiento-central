from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit, QGroupBox, QMessageBox
)
from PySide6.QtCore import QDate, Qt
from controllers.reportes_controller import obtener_reportes, exportar_pdf

class ReportesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📊 Reportes de Ingresos y Salidas")
        self.setFixedSize(900, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()        
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 🔷 Encabezado
        titulo = QLabel("📊 Reportes detallados de movimiento de vehículos")
        titulo.setStyleSheet("font-weight: bold; font-size: 16px; margin: 10px 0;")
        layout.addWidget(titulo)

        # 🔹 Filtros
        filtro_grupo = QGroupBox("🔎 Filtros de búsqueda")
        filtro_layout = QHBoxLayout()
        filtro_layout.setContentsMargins(10, 20, 10, 20)  # Espaciado interno

        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setCalendarPopup(True)
        self.fecha_inicio.setDate(QDate.currentDate())

        self.fecha_fin = QDateEdit()
        self.fecha_fin.setCalendarPopup(True)
        self.fecha_fin.setDate(QDate.currentDate())

        self.input_patente = QLineEdit()
        self.input_patente.setPlaceholderText("Patente (opcional)")

        self.btn_filtrar = QPushButton("🔍 Buscar")
        self.btn_filtrar.setStyleSheet("padding: 6px;")
        self.btn_filtrar.clicked.connect(self.buscar_reportes)

        self.btn_exportar = QPushButton("📤 Exportar PDF")
        self.btn_exportar.setStyleSheet("padding: 6px;")
        self.btn_exportar.clicked.connect(self.exportar_pdf)

        filtro_layout.addWidget(QLabel("Desde:"))
        filtro_layout.addWidget(self.fecha_inicio)
        filtro_layout.addWidget(QLabel("Hasta:"))
        filtro_layout.addWidget(self.fecha_fin)
        filtro_layout.addWidget(self.input_patente)
        filtro_layout.addWidget(self.btn_filtrar)
        filtro_layout.addWidget(self.btn_exportar)

        filtro_grupo.setLayout(filtro_layout)
        layout.addWidget(filtro_grupo)

        # 🔸 Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Patente", "Ingreso", "Salida", "Minutos", "Tarifa"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet("QTableWidget::item { padding: 6px; }")

        layout.addWidget(self.tabla)
        self.setLayout(layout)

    def buscar_reportes(self):
        fecha_inicio = self.fecha_inicio.date().toPython()
        fecha_fin = self.fecha_fin.date().toPython()
        patente = self.input_patente.text().strip().upper()

        datos = obtener_reportes(fecha_inicio, fecha_fin, patente)
        self.tabla.setRowCount(len(datos))

        for fila, row in enumerate(datos):
            self.tabla.setItem(fila, 0, QTableWidgetItem(row["patente"]))
            self.tabla.setItem(fila, 1, QTableWidgetItem(str(row["fecha_hora_ingreso"])))
            self.tabla.setItem(fila, 2, QTableWidgetItem(str(row["fecha_hora_salida"])))
            self.tabla.setItem(fila, 3, QTableWidgetItem(str(row["minutos"])))
            self.tabla.setItem(fila, 4, QTableWidgetItem(f"${row['tarifa_aplicada']:.0f}"))

        self.resultados = datos

    def exportar_pdf(self):
        if hasattr(self, "resultados") and self.resultados:
            exportar_pdf(self.resultados)
        else:
            QMessageBox.information(self, "Aviso", "Primero realiza una búsqueda para poder exportar.")
