from views.login import LoginWindow
from views.setup_window import SetupWindow
from controllers.login_controller import hay_usuarios_registrados
from PySide6.QtWidgets import QApplication
from styles import GLOBAL_STYLESHEET
from utils.file_cleanup import ejecutar_limpieza_periodica
from utils.update_notifier import schedule_startup_update_check
import sys


def mostrar_login():
    login = LoginWindow()
    login.show()
    return login  # Importante para mantener referencia


if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyleSheet(GLOBAL_STYLESHEET)

    try:
        resultado_limpieza = ejecutar_limpieza_periodica()
        if resultado_limpieza.get("ejecutada"):
            print(f"Limpieza de archivos: {resultado_limpieza['eliminados']} eliminados.")
    except Exception as e:
        print(f"No se pudo ejecutar la limpieza de archivos: {e}")

    if hay_usuarios_registrados():
        print("Usuarios encontrados. Abriendo LoginWindow.")
        ventana = LoginWindow()
    else:
        print("No hay usuarios. Abriendo SetupWindow.")
        ventana = SetupWindow(mostrar_login)

    ventana.show()
    schedule_startup_update_check(ventana)
    sys.exit(app.exec())
