from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTimeEdit, 
    QSpinBox, QHBoxLayout, QPushButton
)
from PySide6.QtCore import QTime

class SubidaDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Definir Subida Temporal de Precios")
        self.setFixedSize(300, 300)

        layout = QVBoxLayout()

        # Hora de inicio
        layout.addWidget(QLabel("Hora de inicio:"))
        self.hora_inicio = QTimeEdit()
        self.hora_inicio.setDisplayFormat("HH:mm")
        self.hora_inicio.setTime(QTime.currentTime())
        layout.addWidget(self.hora_inicio)

        # Hora de término
        layout.addWidget(QLabel("Hora de término:"))
        self.hora_fin = QTimeEdit()
        self.hora_fin.setDisplayFormat("HH:mm")
        self.hora_fin.setTime(QTime.currentTime().addSecs(3600))
        layout.addWidget(self.hora_fin)

        # Monto adicional
        layout.addWidget(QLabel("Monto adicional a aplicar ($CLP):"))
        self.monto_extra = QSpinBox()
        self.monto_extra.setMinimum(1)
        self.monto_extra.setMaximum(10000)
        self.monto_extra.setValue(100)
        layout.addWidget(self.monto_extra)

        # Botones
        botones_layout = QHBoxLayout()
        self.btn_ok = QPushButton("Aceptar")
        self.btn_cancel = QPushButton("Cancelar")
        botones_layout.addWidget(self.btn_ok)
        botones_layout.addWidget(self.btn_cancel)

        layout.addLayout(botones_layout)

        self.setLayout(layout)

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def obtener_datos(self):
        return (
            self.hora_inicio.time().toString("HH:mm"),
            self.hora_fin.time().toString("HH:mm"),
            self.monto_extra.value()
        )
