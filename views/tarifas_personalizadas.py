from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QInputDialog, QMessageBox
)
from controllers.tarifas_controller import (
    obtener_tarifas_personalizadas,
    agregar_intervalo,
    eliminar_intervalo,
    actualizar_intervalo
)

class TarifasPersonalizadasWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tarifas Personalizadas")
        self.setFixedSize(600, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Botones
        botones_layout = QHBoxLayout()
        self.btn_agregar = QPushButton("Agregar intervalo")
        self.btn_agregar.clicked.connect(self.agregar)
        self.btn_actualizar = QPushButton("Actualizar seleccionado")
        self.btn_actualizar.clicked.connect(self.actualizar)
        self.btn_eliminar = QPushButton("Eliminar seleccionado")
        self.btn_eliminar.clicked.connect(self.eliminar)

        botones_layout.addWidget(self.btn_agregar)
        botones_layout.addWidget(self.btn_actualizar)
        botones_layout.addWidget(self.btn_eliminar)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["ID", "Desde (min)", "Hasta (min)", "Valor (CLP)"])
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addLayout(botones_layout)
        layout.addWidget(self.tabla)
        self.setLayout(layout)

        self.cargar_datos()

    def cargar_datos(self):
        self.tabla.setRowCount(0)
        datos = obtener_tarifas_personalizadas()
        for i, row in enumerate(datos):
            self.tabla.insertRow(i)
            self.tabla.setItem(i, 0, QTableWidgetItem(str(row["id_tarifa"])))
            self.tabla.setItem(i, 1, QTableWidgetItem(str(row["minuto_inicio"])))
            self.tabla.setItem(i, 2, QTableWidgetItem(str(row["minuto_fin"])))
            self.tabla.setItem(i, 3, QTableWidgetItem(str(row["valor"])))

    def agregar(self):
        min_inicio, ok1 = QInputDialog.getInt(self, "Nuevo intervalo", "Desde (minutos):", 0)
        if not ok1: return
        min_fin, ok2 = QInputDialog.getInt(self, "Nuevo intervalo", "Hasta (minutos):", min_inicio+1)
        if not ok2: return
        valor, ok3 = QInputDialog.getInt(self, "Nuevo intervalo", "Valor (CLP):", 0)
        if not ok3: return

        agregar_intervalo(min_inicio, min_fin, valor)
        self.cargar_datos()

    def eliminar(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atención", "Selecciona una fila primero.")
            return

        id_tarifa = int(self.tabla.item(fila, 0).text())
        eliminar_intervalo(id_tarifa)
        self.cargar_datos()

    def actualizar(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atención", "Selecciona una fila primero.")
            return

        id_tarifa = int(self.tabla.item(fila, 0).text())
        min_inicio, ok1 = QInputDialog.getInt(self, "Editar", "Desde (min):", int(self.tabla.item(fila, 1).text()))
        if not ok1: return
        min_fin, ok2 = QInputDialog.getInt(self, "Editar", "Hasta (min):", int(self.tabla.item(fila, 2).text()))
        if not ok2: return
        valor, ok3 = QInputDialog.getInt(self, "Editar", "Valor (CLP):", int(self.tabla.item(fila, 3).text()))
        if not ok3: return

        actualizar_intervalo(id_tarifa, min_inicio, min_fin, valor)
        self.cargar_datos()
