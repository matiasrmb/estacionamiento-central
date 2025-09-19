from views.login import LoginWindow
from views.setup_window import SetupWindow
from controllers.login_controller import hay_usuarios_registrados
from PySide6.QtWidgets import QApplication
import sys


def mostrar_login():
    login = LoginWindow()
    login.show()
    return login  # Importante para mantener referencia


if __name__ == "__main__":
    app = QApplication(sys.argv)
    with open("styles/estilos.qss", "r") as f:
        app.setStyleSheet(f.read())

    if hay_usuarios_registrados():
        print("✅ Usuarios encontrados. Abriendo LoginWindow.")
        ventana = LoginWindow()
    else:
        print("🆕 No hay usuarios. Abriendo SetupWindow.")
        ventana = SetupWindow(mostrar_login)

    ventana.show()
    sys.exit(app.exec())
