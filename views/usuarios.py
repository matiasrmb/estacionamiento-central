from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHBoxLayout, QLineEdit, QComboBox, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt
from controllers.usuarios_controller import obtener_usuarios, crear_usuario, cambiar_contrasena
from functools import partial

class UsuariosWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Usuarios")
        self.setMinimumSize(500, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Título
        titulo = QLabel("Usuarios Registrados")
        titulo.setStyleSheet("font-weight: bold; font-size: 16px")
        layout.addWidget(titulo)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Usuario", "Rol", "Acción"])
        layout.addWidget(self.tabla)

        # Formulario para crear usuario
        form_layout = QHBoxLayout()
        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Nuevo usuario")
        self.input_clave = QLineEdit()
        self.input_clave.setPlaceholderText("Contraseña")
        self.input_clave.setEchoMode(QLineEdit.Password)
        self.select_rol = QComboBox()
        self.select_rol.addItems(["operador", "administrador"])
        btn_crear = QPushButton("Crear")
        btn_crear.clicked.connect(self.crear_usuario)

        form_layout.addWidget(self.input_usuario)
        form_layout.addWidget(self.input_clave)
        form_layout.addWidget(self.select_rol)
        form_layout.addWidget(btn_crear)

        layout.addLayout(form_layout)
        self.setLayout(layout)

        # Cargar datos
        self.cargar_usuarios()

    def cargar_usuarios(self):
        usuarios = obtener_usuarios()
        self.tabla.setRowCount(len(usuarios))
        for i, u in enumerate(usuarios):
            self.tabla.setItem(i, 0, QTableWidgetItem(u["usuario"]))
            self.tabla.setItem(i, 1, QTableWidgetItem(u["rol"]))
            btn_cambiar = QPushButton("🔒 Cambiar clave")
            btn_cambiar.clicked.connect(partial(self.preguntar_nueva_clave, u["usuario"]))
            self.tabla.setCellWidget(i, 2, btn_cambiar)

    def crear_usuario(self):
        usuario = self.input_usuario.text().strip()
        clave = self.input_clave.text().strip()
        rol = self.select_rol.currentText()

        if not usuario or not clave:
            QMessageBox.warning(self, "Campos vacíos", "Debes ingresar usuario y contraseña.")
            return

        if crear_usuario(usuario, clave, rol):
            QMessageBox.information(self, "Éxito", "Usuario creado correctamente.")
            self.input_usuario.clear()
            self.input_clave.clear()
            self.cargar_usuarios()
        else:
            QMessageBox.critical(self, "Error", "No se pudo crear el usuario.")

    def preguntar_nueva_clave(self, usuario):
        clave, ok = QInputDialog.getText(self, "Cambiar contraseña", f"Ingresar nueva clave para '{usuario}':", QLineEdit.Password)
        if ok and clave:
            if cambiar_contrasena(usuario, clave):
                QMessageBox.information(self, "Éxito", "Contraseña actualizada.")
            else:
                QMessageBox.critical(self, "Error", "No se pudo cambiar la contraseña.")
