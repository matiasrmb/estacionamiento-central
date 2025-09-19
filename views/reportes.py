from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, 
    QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QHeaderView, QDateEdit, 
    QGroupBox, QMessageBox, QCheckBox
)
from PySide6.QtCore import QDate, Qt
from controllers.reportes_controller import obtener_reportes, exportar_pdf

class ReportesWindow(QWidget):
    """
    Ventana para visualizar y exportar reportes de ingresos y salidas de vehículos,
    con filtros por rango de fechas y patente y exportarlos a un archivo PDF.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📊 Reportes de Ingresos y Salidas")
        self.setFixedSize(900, 600) 
        self.resultados = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Filtro de fechas y patente
        filtro_layout = QHBoxLayout()

        filtro_layout.addWidget(QLabel("📅 Desde:"))
        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setDate(QDate.currentDate())
        self.fecha_inicio.setCalendarPopup(True)
        filtro_layout.addWidget(self.fecha_inicio)

        filtro_layout.addWidget(QLabel("📅 Hasta:"))
        self.fecha_fin = QDateEdit()
        self.fecha_fin.setDate(QDate.currentDate())
        self.fecha_fin.setCalendarPopup(True)
        filtro_layout.addWidget(self.fecha_fin)

        filtro_layout.addWidget(QLabel("🚗 Patente:"))
        self.input_patente = QLineEdit()
        self.input_patente.setPlaceholderText("Opcional")
        filtro_layout.addWidget(self.input_patente)

        self.boton_filtrar = QPushButton("🔍 Buscar")
        self.boton_filtrar.clicked.connect(self.filtrar)
        filtro_layout.addWidget(self.boton_filtrar)

        layout.addLayout(filtro_layout)

        # Tabla de resultados
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Patente", "Ingreso", "Salida", "Minutos", "Monto"])
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet("QTableWidget { font-size: 13px; }")
        layout.addWidget(self.tabla)

        # Botón de exportar PDF
        self.boton_exportar = QPushButton("🖨️ Exportar PDF")
        self.boton_exportar.setEnabled(False)
        self.boton_exportar.clicked.connect(self.exportar_pdf)
        layout.addWidget(self.boton_exportar)

        self.setLayout(layout)

    def filtrar(self):
        """
        Realiza la consulta de reportes según los filtros ingresados.
        Actualiza la tabla con los resultados.
        """
        fecha_inicio = self.fecha_inicio.date().toPython()
        fecha_fin = self.fecha_fin.date().toPython()
        patente = self.input_patente.text().strip().upper()

        self.resultados = obtener_reportes(fecha_inicio, fecha_fin, patente)

        if not self.resultados:
            QMessageBox.information(self, "Sin resultados", "No se encontraron movimientos en ese rango.")
            self.tabla.setRowCount(0)
            self.boton_exportar.setEnabled(False)
            return

        self.tabla.setRowCount(len(self.resultados))
        total = 0

        for i, row in enumerate(self.resultados):
            ingreso = row["fecha_hora_ingreso"].strftime("%d-%m-%Y %H:%M")
            salida = row["fecha_hora_salida"].strftime("%d-%m-%Y %H:%M")
            tarifa = row["tarifa_aplicada"]
            total += tarifa

            self.tabla.setItem(i, 0, QTableWidgetItem(row["patente"]))
            self.tabla.setItem(i, 1, QTableWidgetItem(ingreso))
            self.tabla.setItem(i, 2, QTableWidgetItem(salida))
            self.tabla.setItem(i, 3, QTableWidgetItem(str(row["minutos"])))
            self.tabla.setItem(i, 4, QTableWidgetItem(f"${tarifa:.0f}"))

        # Fila extra para total
        self.tabla.insertRow(self.tabla.rowCount())
        fila_total = self.tabla.rowCount() - 1

        item_total_label = QTableWidgetItem("TOTAL RECAUDADO:")
        item_total_label.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_total_label.setFlags(Qt.ItemIsEnabled)
        self.tabla.setItem(fila_total, 3, item_total_label)

        item_total_valor = QTableWidgetItem(f"${total:.0f}")
        item_total_valor.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        item_total_valor.setFlags(Qt.ItemIsEnabled)
        self.tabla.setItem(fila_total, 4, item_total_valor)

        self.boton_exportar.setEnabled(True)

    def exportar_pdf(self):
        if hasattr(self, "resultados") and self.resultados:
            exportar_pdf(self.resultados)
        else:
            QMessageBox.information(self, "Aviso", "Primero realiza una búsqueda para poder exportar.")
