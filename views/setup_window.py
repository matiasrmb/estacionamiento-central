from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMessageBox
)
from controllers.usuarios_controller import crear_usuario

class SetupWindow(QWidget):
    """
    Ventana de configuración inicial para crear el primer usuario administrador.
    Esta ventana se muestra solo si no existen usuarios en el sistema.
    """
    def __init__(self, callback_mostrar_login):
        super().__init__()
        self.callback_mostrar_login = callback_mostrar_login 
        self.setWindowTitle("Configuración Inicial - Crear Usuario")
        self.setFixedSize(900, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Campo de usuario
        label_usuario = QLabel("👤 Nombre de usuario:")
        label_usuario.setStyleSheet("font-weight: bold;")
        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Ingrese el nombre de usuario")

        # Campo de contraseña
        label_clave = QLabel("🔑 Contraseña:")
        label_clave.setStyleSheet("font-weight: bold;")
        self.input_clave = QLineEdit()
        self.input_clave.setEchoMode(QLineEdit.Password)
        self.input_clave.setPlaceholderText("*********")

        # Selección de rol
        label_rol = QLabel("🔐 Rol:")
        label_rol.setStyleSheet("font-weight: bold;")
        self.combo_rol = QComboBox()
        self.combo_rol.addItems(["administrador", "operador"])

        # Botón de crear usuario
        self.btn_crear = QPushButton("Crear usuario")
        self.btn_crear.clicked.connect(self.crear_usuario)

        layout.addWidget(label_usuario)
        layout.addWidget(self.input_usuario)

        layout.addWidget(label_clave)
        layout.addWidget(self.input_clave)

        layout.addWidget(label_rol)
        layout.addWidget(self.combo_rol)

        layout.addStretch()
        layout.addWidget(self.btn_crear)

        self.setLayout(layout)

    def crear_usuario(self):
        """
        Crea el primer usuario administrador y cierra la ventana de configuración.
        """
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
            self.callback_mostrar_login()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear el usuario.\n{e}")
