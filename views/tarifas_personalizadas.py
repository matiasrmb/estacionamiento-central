from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QInputDialog, 
    QMessageBox, QLabel, QGroupBox
)
from PySide6.QtCore import Qt
from controllers.tarifas_controller import (
    obtener_tarifas_personalizadas, agregar_intervalo,
    eliminar_intervalo, actualizar_intervalo
)

class TarifasPersonalizadasWindow(QWidget):
    """
    Ventana que permite configurar los tramos personalizados de tarifas
    por tiempo de estacionamiento. Solo accesible para administradores.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editor de Tarifas Personalizadas")
        self.setMinimumSize(900, 600) 
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título principal
        self.label_titulo = QLabel("📐 Configuración de Tramos de Tarifas")
        self.label_titulo.setObjectName("TituloVentana")
        self.label_titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_titulo)

        # Grupo de botones de acción
        grupo_botones = QGroupBox("⚙️ Acciones disponibles")
        botones_layout = QHBoxLayout()
        botones_layout.setContentsMargins(10, 20, 10, 20)

        self.btn_agregar = QPushButton("➕ Agregar intervalo")
        self.btn_agregar.setMinimumHeight(38)
        self.btn_agregar.clicked.connect(self.agregar)

        self.btn_actualizar = QPushButton("✏️ Actualizar seleccionado")
        self.btn_actualizar.setMinimumHeight(38)
        self.btn_actualizar.clicked.connect(self.actualizar)

        self.btn_eliminar = QPushButton("🗑️ Eliminar seleccionado")
        self.btn_eliminar.setMinimumHeight(38)
        self.btn_eliminar.clicked.connect(self.eliminar)

        botones_layout.addWidget(self.btn_agregar)
        botones_layout.addWidget(self.btn_actualizar)
        botones_layout.addWidget(self.btn_eliminar)
        grupo_botones.setLayout(botones_layout)
        layout.addWidget(grupo_botones)

        # Tabla de tarifas personalizadas
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["ID", "Desde (min)", "Hasta (min)", "Valor (CLP)"])
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.verticalHeader().setDefaultSectionSize(36)
        self.tabla.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.tabla)
        self.setLayout(layout)

        self.cargar_datos()

    def cargar_datos(self):
        """Carga los tramos personalizados desde la base de datos a la tabla."""
        self.tabla.setRowCount(0)
        datos = obtener_tarifas_personalizadas()

        for i, row in enumerate(datos):
            self.tabla.insertRow(i)
            self.tabla.setItem(i, 0, QTableWidgetItem(str(row["id_tarifa"])))
            self.tabla.setItem(i, 1, QTableWidgetItem(str(row["minuto_inicio"])))
            self.tabla.setItem(i, 2, QTableWidgetItem(str(row["minuto_fin"])))
            self.tabla.setItem(i, 3, QTableWidgetItem(str(row["valor"])))

    def agregar(self):
        """Agrega un nuevo tramo de tarifa personalizada."""
        min_inicio, ok1 = QInputDialog.getInt(self, "Nuevo intervalo", "Desde (minutos):", 0)
        if not ok1:
            return

        min_fin, ok2 = QInputDialog.getInt(self, "Nuevo intervalo", "Hasta (minutos):", min_inicio + 1)
        if not ok2:
            return

        valor, ok3 = QInputDialog.getInt(self, "Nuevo intervalo", "Valor (CLP):", 0)
        if not ok3:
            return

        agregar_intervalo(min_inicio, min_fin, valor)
        self.cargar_datos()

    def eliminar(self):
        """Elimina el tramo de tarifa personalizada seleccionado."""
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atención", "Selecciona una fila primero.")
            return

        id_tarifa = int(self.tabla.item(fila, 0).text())
        eliminar_intervalo(id_tarifa)
        self.cargar_datos()

    def actualizar(self):
        """Actualiza el tramo de tarifa personalizada seleccionado."""
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atención", "Selecciona una fila primero.")
            return

        id_tarifa = int(self.tabla.item(fila, 0).text())

        min_inicio_actual = int(self.tabla.item(fila, 1).text())
        min_fin_actual = int(self.tabla.item(fila, 2).text())
        valor_actual = int(self.tabla.item(fila, 3).text())

        min_inicio, ok1 = QInputDialog.getInt(
            self, "Editar intervalo", "Desde (minutos):", min_inicio_actual
        )
        if not ok1:
            return

        min_fin, ok2 = QInputDialog.getInt(
            self, "Editar intervalo", "Hasta (minutos):", min_fin_actual
        )
        if not ok2:
            return

        valor, ok3 = QInputDialog.getInt(
            self, "Editar intervalo", "Valor (CLP):", valor_actual
        )
        if not ok3:
            return

        actualizar_intervalo(id_tarifa, min_inicio, min_fin, valor)
        self.cargar_datos()
