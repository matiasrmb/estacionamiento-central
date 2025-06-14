from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
)
import sys
from controllers.login_controller import validar_usuario
from views.main_window import MainWindow

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inicio de Sesión - Estacionamiento Central")
        self.setGeometry(100, 100, 300, 100)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.user_label = QLabel("Usuario:")
        self.user_input = QLineEdit()

        self.pass_label = QLabel("Contraseña:")
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton("Ingresar")
        self.login_button.clicked.connect(self.validar_credenciales)

        layout.addWidget(self.user_label)
        layout.addWidget(self.user_input)
        layout.addWidget(self.pass_label)
        layout.addWidget(self.pass_input)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def validar_credenciales(self):
        usuario = self.user_input.text()
        clave = self.pass_input.text()

        exito, rol = validar_usuario(usuario,clave)
        if exito:
            QMessageBox.information(self, "Acceso correcto", f"Bienvenido, {usuario}. Rol: {rol}")
            self.hide()
            self.main_window = MainWindow(usuario, rol)
            self.main_window.show()
        else:
            QMessageBox.critical(self, "Error", "Usuario o clave incorrectas.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = LoginWindow()
    ventana.show()
    sys.exit(app.exec())