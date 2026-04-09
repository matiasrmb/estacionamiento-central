from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt


class CambiarClaveDialog(QDialog):
    """
    Diálogo para cambiar o restablecer la contraseña de un usuario.
    Incluye confirmación y opción para mostrar/ocultar contraseña.
    """

    def __init__(self, usuario, parent=None):
        super().__init__(parent)
        self.usuario = usuario
        self.setWindowTitle("Cambiar contraseña")
        self.setModal(True)
        self.setFixedSize(420, 230)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        titulo = QLabel(f"Nueva contraseña para: {self.usuario}")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        self.input_clave = QLineEdit()
        self.input_clave.setPlaceholderText("Nueva contraseña")
        self.input_clave.setEchoMode(QLineEdit.Password)
        self.input_clave.setMinimumHeight(38)

        self.input_confirmar = QLineEdit()
        self.input_confirmar.setPlaceholderText("Confirmar contraseña")
        self.input_confirmar.setEchoMode(QLineEdit.Password)
        self.input_confirmar.setMinimumHeight(38)

        self.btn_toggle = QPushButton("Mostrar")
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setMinimumHeight(36)
        self.btn_toggle.clicked.connect(self.toggle_password_visibility)

        layout.addWidget(self.input_clave)
        layout.addWidget(self.input_confirmar)
        layout.addWidget(self.btn_toggle)

        botones = QHBoxLayout()
        botones.setSpacing(10)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setMinimumHeight(38)
        self.btn_cancelar.clicked.connect(self.reject)

        self.btn_aceptar = QPushButton("Guardar")
        self.btn_aceptar.setMinimumHeight(38)
        self.btn_aceptar.clicked.connect(self.validar_y_aceptar)

        botones.addWidget(self.btn_cancelar)
        botones.addWidget(self.btn_aceptar)

        layout.addLayout(botones)
        self.setLayout(layout)

        self.input_clave.returnPressed.connect(self.input_confirmar.setFocus)
        self.input_confirmar.returnPressed.connect(self.validar_y_aceptar)

    def toggle_password_visibility(self):
        """
        Alterna entre mostrar y ocultar las contraseñas.
        """
        visible = self.btn_toggle.isChecked()
        modo = QLineEdit.Normal if visible else QLineEdit.Password

        self.input_clave.setEchoMode(modo)
        self.input_confirmar.setEchoMode(modo)
        self.btn_toggle.setText("Ocultar" if visible else "Mostrar")

    def validar_y_aceptar(self):
        """
        Valida los campos antes de cerrar el diálogo con éxito.
        """
        clave = self.input_clave.text().strip()
        confirmar = self.input_confirmar.text().strip()

        if not clave or not confirmar:
            QMessageBox.warning(self, "Campos requeridos", "Debes completar ambos campos.")
            return

        if clave != confirmar:
            QMessageBox.warning(self, "Contraseñas distintas", "Las contraseñas no coinciden.")
            return

        if len(clave) < 4:
            QMessageBox.warning(
                self,
                "Contraseña inválida",
                "La contraseña debe tener al menos 4 caracteres."
            )
            return

        self.accept()

    def obtener_clave(self):
        """
        Devuelve la contraseña ingresada.

        Returns:
            str: Nueva contraseña validada.
        """
        return self.input_clave.text().strip()