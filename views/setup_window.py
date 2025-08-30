from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMessageBox
)
from controllers.usuarios_controller import crear_usuario

class SetupWindow(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWindowTitle("Configuración Inicial - Crear Usuario")
        self.setFixedSize(350, 250)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("👤 Nombre de usuario:"))
        self.input_usuario = QLineEdit()

        layout.addWidget(self.input_usuario)

        layout.addWidget(QLabel("🔑 Contraseña:"))
        self.input_clave = QLineEdit()
        self.input_clave.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.input_clave)

        layout.addWidget(QLabel("🔐 Rol:"))
        self.combo_rol = QComboBox()
        self.combo_rol.addItems(["administrador", "operador"])
        layout.addWidget(self.combo_rol)

        self.btn_crear = QPushButton("Crear usuario")
        self.btn_crear.clicked.connect(self.crear_usuario)
        layout.addWidget(self.btn_crear)

        self.setLayout(layout)

    def crear_usuario(self):
        usuario = self.input_usuario.text().strip()
        clave = self.input_clave.text().strip()
        rol = self.combo_rol.currentText()

        if not usuario or not clave:
            QMessageBox.warning(self, "Campos requeridos", "Debes ingresar usuario y contraseña.")
            return

        try:
            crear_usuario(usuario, clave, rol)
            QMessageBox.information(self, "Éxito", f"Usuario '{usuario}' creado.")
            self.close()
            self.app.mostrar_login()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear el usuario.\n{e}")
