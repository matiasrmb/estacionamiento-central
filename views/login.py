from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, 
    QPushButton, QVBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt
import sys

from controllers.login_controller import validar_usuario
from views.main_window import MainWindow
from views.dashboard import DashboardWindow

class LoginWindow(QWidget):
    """
    Ventana de inicio de sesión del sistema Estacionamiento Central.
    Permite al usuario ingresar su usuario y contraseña para validar el acceso.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inicio de Sesión - Estacionamiento Central")
        self.setFixedSize(450, 360)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(10)

        # Título
        titulo = QLabel("🅿️ Estacionamiento Central")
        titulo.setObjectName("TituloVentana")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        # Etiqueta y campo de usuario
        self.user_label = QLabel("Usuario:")
        self.user_input = QLineEdit()
        self.user_input.setMinimumHeight(35)
        self.user_input.setPlaceholderText("Ingresa tu usuario")

        # Etiqueta y campo de contraseña
        self.pass_label = QLabel("Contraseña:")
        self.pass_input = QLineEdit()
        self.pass_input.setMinimumHeight(35)
        self.pass_input.setPlaceholderText("Ingresa tu contraseña")
        self.pass_input.setEchoMode(QLineEdit.Password)

        # Botón de inicio de sesión
        self.login_button = QPushButton("Ingresar")
        self.login_button.setMinimumHeight(35)
        self.login_button.clicked.connect(self.validar_credenciales)

        # Añadir al layout
        layout.addWidget(self.user_label)
        layout.addWidget(self.user_input)
        layout.addSpacing(10)
        layout.addWidget(self.pass_label)
        layout.addWidget(self.pass_input)
        layout.addSpacing(15)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def validar_credenciales(self):
        """
        Valida las credenciales ingresadas por el usuario.
        Según el resultado, muestra mensajes o redirige al dashboard.
        """
        usuario = self.user_input.text()
        clave = self.pass_input.text()

        if not usuario or not clave:
            QMessageBox.warning(self, "Campos requeridos", "Debes ingresar usuario y contraseña.")
            return

        exito, rol = validar_usuario(usuario, clave)

        if exito is True:
            QMessageBox.information(self, "Acceso correcto", f"Bienvenido, {usuario}. Rol: {rol}")
            self.hide()
            self.dashboard = DashboardWindow(usuario, rol)
            self.dashboard.show()
        elif exito == "inactivo":
            QMessageBox.warning(self, "Cuenta inactiva", "Tu cuenta está desactivada. Contacta al administrador.")
        else:
            QMessageBox.critical(self, "Error", "Usuario o clave incorrectas.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = LoginWindow()
    ventana.show()
    sys.exit(app.exec())
