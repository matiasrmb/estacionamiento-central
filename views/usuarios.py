from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHBoxLayout,
    QLineEdit, QComboBox, QMessageBox,
    QInputDialog, QGroupBox, QHeaderView
)
from PySide6.QtCore import Qt
from controllers.usuarios_controller import (
    obtener_usuarios, crear_usuario,
    cambiar_contrasena, cambiar_estado_usuario
)
from functools import partial


class UsuariosWindow(QWidget):
    """
    Vista para la gestión de usuarios del sistema.
    Permite ver, crear, activar/desactivar y cambiar contraseñas.
    """

    def __init__(self):
        super().__init__()
        self.setMinimumSize(900, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        titulo = QLabel("Gestión de usuarios")
        titulo.setObjectName("TituloVentana")
        titulo.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(titulo)

        subtitulo = QLabel("Administra cuentas de operadores y administradores del sistema.")
        subtitulo.setObjectName("SubtituloSeccion")
        subtitulo.setWordWrap(True)
        layout.addWidget(subtitulo)

        # =========================================================
        # TABLA
        # =========================================================
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Usuario", "Rol", "Acciones"])
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.verticalHeader().setDefaultSectionSize(58)

        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        layout.addWidget(self.tabla)

        # =========================================================
        # FORMULARIO
        # =========================================================
        grupo_formulario = QGroupBox("Crear nuevo usuario")
        form_layout = QHBoxLayout()
        form_layout.setContentsMargins(12, 20, 12, 20)
        form_layout.setSpacing(10)

        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Usuario")
        self.input_usuario.setMinimumHeight(38)

        self.input_clave = QLineEdit()
        self.input_clave.setPlaceholderText("Contraseña")
        self.input_clave.setEchoMode(QLineEdit.Password)
        self.input_clave.setMinimumHeight(38)

        self.select_rol = QComboBox()
        self.select_rol.addItems(["Operador", "Administrador"])
        self.select_rol.setMinimumHeight(38)

        self.btn_crear = QPushButton("Crear usuario")
        self.btn_crear.setMinimumHeight(38)
        self.btn_crear.clicked.connect(self.crear_usuario)

        form_layout.addWidget(self.input_usuario)
        form_layout.addWidget(self.input_clave)
        form_layout.addWidget(self.select_rol)
        form_layout.addWidget(self.btn_crear)

        grupo_formulario.setLayout(form_layout)
        layout.addWidget(grupo_formulario)

        self.setLayout(layout)
        self.cargar_usuarios()

    def cargar_usuarios(self):
        usuarios = obtener_usuarios()
        self.tabla.setRowCount(len(usuarios))

        for i, u in enumerate(usuarios):
            item_usuario = QTableWidgetItem(u["usuario"])
            item_rol = QTableWidgetItem(u["rol"])

            item_usuario.setTextAlignment(Qt.AlignCenter)
            item_rol.setTextAlignment(Qt.AlignCenter)

            self.tabla.setItem(i, 0, item_usuario)
            self.tabla.setItem(i, 1, item_rol)

            botones = QWidget()
            layout_btn = QHBoxLayout()
            layout_btn.setContentsMargins(8, 6, 8, 6)
            layout_btn.setSpacing(8)
            layout_btn.setAlignment(Qt.AlignCenter)

            btn_clave = QPushButton("Cambiar clave")
            btn_clave.setObjectName("BotonTabla")
            btn_clave.setMinimumHeight(34)
            btn_clave.setMinimumWidth(120)
            btn_clave.clicked.connect(partial(self.preguntar_nueva_clave, u["usuario"]))

            estado_texto = "Desactivar" if u["activo"] else "Activar"
            btn_estado = QPushButton(estado_texto)
            btn_estado.setMinimumHeight(34)
            btn_estado.setMinimumWidth(100)

            if u["activo"]:
                btn_estado.setObjectName("BotonTablaPeligro")
            else:
                btn_estado.setObjectName("BotonTabla")

            btn_estado.clicked.connect(
                partial(self.toggle_estado_usuario, u["usuario"], not u["activo"])
            )

            layout_btn.addWidget(btn_clave)
            layout_btn.addWidget(btn_estado)

            botones.setLayout(layout_btn)
            self.tabla.setCellWidget(i, 2, botones)

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
        clave, ok = QInputDialog.getText(
            self,
            "Cambiar contraseña",
            f"Ingresar nueva clave para '{usuario}':",
            QLineEdit.Password
        )
        if ok and clave:
            if cambiar_contrasena(usuario, clave):
                QMessageBox.information(self, "Éxito", "Contraseña actualizada.")
            else:
                QMessageBox.critical(self, "Error", "No se pudo cambiar la contraseña.")

    def toggle_estado_usuario(self, usuario, nuevo_estado):
        texto = "activar" if nuevo_estado else "desactivar"
        confirmar = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Seguro que deseas {texto} el usuario '{usuario}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirmar == QMessageBox.Yes:
            if cambiar_estado_usuario(usuario, nuevo_estado):
                QMessageBox.information(self, "Éxito", "Estado actualizado.")
                self.cargar_usuarios()
            else:
                QMessageBox.critical(self, "Error", "No se pudo actualizar el estado.")