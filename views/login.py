from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
import sys

from controllers.login_controller import validar_usuario
from views.main_window import MainWindow


class LoginWindow(QWidget):
    """
    Ventana de inicio de sesión del sistema Estacionamiento Central.
    Permite al usuario ingresar su usuario y contraseña para validar el acceso.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inicio de sesión - Estacionamiento Central")
        self.setFixedSize(460, 380)
        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout()
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(0)

        card = QFrame()
        card.setObjectName("CardAcceso")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        titulo = QLabel("Estacionamiento Central")
        titulo.setObjectName("TituloAcceso")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        subtitulo = QLabel("Ingresa tus credenciales para acceder al sistema.")
        subtitulo.setObjectName("SubtituloAcceso")
        subtitulo.setAlignment(Qt.AlignCenter)
        subtitulo.setWordWrap(True)
        layout.addWidget(subtitulo)

        layout.addSpacing(8)

        self.user_label = QLabel("Usuario")
        self.user_input = QLineEdit()
        self.user_input.setMinimumHeight(38)
        self.user_input.setPlaceholderText("Ingresa tu usuario")

        self.pass_label = QLabel("Contraseña")
        self.pass_input = QLineEdit()
        self.pass_input.setMinimumHeight(38)
        self.pass_input.setPlaceholderText("Ingresa tu contraseña")
        self.pass_input.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton("Ingresar")
        self.login_button.setMinimumHeight(40)
        self.login_button.clicked.connect(self.validar_credenciales)

        layout.addWidget(self.user_label)
        layout.addWidget(self.user_input)
        layout.addSpacing(6)
        layout.addWidget(self.pass_label)
        layout.addWidget(self.pass_input)
        layout.addSpacing(14)
        layout.addWidget(self.login_button)

        layout_principal.addWidget(card)
        self.setLayout(layout_principal)

        self.user_input.returnPressed.connect(self.pass_input.setFocus)
        self.pass_input.returnPressed.connect(self.validar_credenciales)
        self.user_input.setFocus()

    def validar_credenciales(self):
        """
        Valida las credenciales ingresadas por el usuario.
        Según el resultado, muestra mensajes o redirige a la app principal.
        """
        usuario = self.user_input.text().strip()
        clave = self.pass_input.text().strip()

        if not usuario or not clave:
            QMessageBox.warning(self, "Campos requeridos", "Debes ingresar usuario y contraseña.")
            return

        exito, rol = validar_usuario(usuario, clave)

        if exito is True:
            QMessageBox.information(self, "Acceso correcto", f"Bienvenido, {usuario}. Rol: {rol}")
            self.hide()
            self.main = MainWindow(usuario, rol)
            self.main.show()
        elif exito == "inactivo":
            QMessageBox.warning(self, "Cuenta inactiva", "Tu cuenta está desactivada. Contacta al administrador.")
        else:
            QMessageBox.critical(self, "Error", "Usuario o clave incorrectas.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = LoginWindow()
    ventana.show()
    sys.exit(app.exec())