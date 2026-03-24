from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMessageBox, QFrame, QGridLayout
)
from PySide6.QtCore import Qt

from controllers.usuarios_controller import crear_usuario


class SetupWindow(QWidget):
    """
    Ventana de configuración inicial para crear el primer usuario del sistema.
    Se muestra solo si no existen usuarios registrados.
    """

    def __init__(self, callback_mostrar_login):
        super().__init__()
        self.callback_mostrar_login = callback_mostrar_login
        self.setWindowTitle("Configuración inicial - Estacionamiento Central")
        self.setFixedSize(720, 500)
        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout()
        layout_principal.setContentsMargins(30, 30, 30, 30)
        layout_principal.setSpacing(0)

        card = QFrame()
        card.setObjectName("CardAcceso")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        titulo = QLabel("Configuración inicial del sistema")
        titulo.setObjectName("TituloAcceso")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        subtitulo = QLabel(
            "Crea el primer usuario para comenzar a utilizar Estacionamiento Central."
        )
        subtitulo.setObjectName("SubtituloAcceso")
        subtitulo.setAlignment(Qt.AlignCenter)
        subtitulo.setWordWrap(True)
        layout.addWidget(subtitulo)

        layout.addSpacing(10)

        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(12)

        label_usuario = QLabel("Nombre de usuario")
        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Ingresa el nombre de usuario")
        self.input_usuario.setMinimumHeight(38)

        label_clave = QLabel("Contraseña")
        self.input_clave = QLineEdit()
        self.input_clave.setEchoMode(QLineEdit.Password)
        self.input_clave.setPlaceholderText("Ingresa una contraseña")
        self.input_clave.setMinimumHeight(38)

        label_rol = QLabel("Rol")
        self.combo_rol = QComboBox()
        self.combo_rol.addItems(["administrador", "operador"])
        self.combo_rol.setMinimumHeight(38)

        form_layout.addWidget(label_usuario, 0, 0)
        form_layout.addWidget(self.input_usuario, 0, 1)
        form_layout.addWidget(label_clave, 1, 0)
        form_layout.addWidget(self.input_clave, 1, 1)
        form_layout.addWidget(label_rol, 2, 0)
        form_layout.addWidget(self.combo_rol, 2, 1)

        form_layout.setColumnStretch(1, 1)

        layout.addLayout(form_layout)
        layout.addSpacing(12)

        self.btn_crear = QPushButton("Crear usuario inicial")
        self.btn_crear.setMinimumHeight(42)
        self.btn_crear.clicked.connect(self.crear_usuario)

        layout.addStretch()
        layout.addWidget(self.btn_crear)

        layout_principal.addWidget(card)
        self.setLayout(layout_principal)

        self.input_usuario.returnPressed.connect(self.input_clave.setFocus)
        self.input_clave.returnPressed.connect(self.crear_usuario)
        self.input_usuario.setFocus()

    def crear_usuario(self):
        """
        Crea el primer usuario del sistema y luego redirige al login.
        """
        usuario = self.input_usuario.text().strip()
        clave = self.input_clave.text().strip()
        rol = self.combo_rol.currentText()

        if not usuario or not clave:
            QMessageBox.warning(self, "Campos requeridos", "Debes ingresar usuario y contraseña.")
            return

        exito = crear_usuario(usuario, clave, rol)

        if exito:
            QMessageBox.information(self, "Éxito", f"Usuario '{usuario}' creado correctamente.")
            self.close()
            self.callback_mostrar_login()
        else:
            QMessageBox.critical(
                self,
                "Error",
                "No se pudo crear el usuario. Verifica la conexión a la base de datos y la existencia de la tabla usuarios."
            )