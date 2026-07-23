from views.login import LoginWindow
from views.setup_window import SetupWindow
from controllers.login_controller import hay_usuarios_registrados
from PySide6.QtWidgets import QApplication, QMessageBox
from styles import GLOBAL_STYLESHEET
from utils.file_cleanup import ejecutar_limpieza_periodica
from utils.logging_config import setup_logging
from utils.update_notifier import schedule_startup_update_check
import logging
import sys


setup_logging()
logger = logging.getLogger(__name__)


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
            logger.info("Limpieza de archivos: %s eliminados.", resultado_limpieza["eliminados"])
    except Exception as e:
        logger.exception("No se pudo ejecutar la limpieza de archivos: %s", e)

    try:
        usuarios_registrados = hay_usuarios_registrados()
    except Exception as e:
        logger.exception("No se pudo verificar usuarios registrados: %s", e)
        QMessageBox.critical(
            None,
            "Error de conexión",
            "No se pudo conectar o verificar la base de datos.\n\n"
            "Revise config.ini, que MySQL esté iniciado y que las credenciales sean correctas.",
        )
        sys.exit(1)

    if usuarios_registrados:
        logger.info("Usuarios encontrados. Abriendo LoginWindow.")
        ventana = LoginWindow()
    else:
        logger.info("No hay usuarios. Abriendo SetupWindow.")
        ventana = SetupWindow(mostrar_login)

    ventana.show()
    schedule_startup_update_check(ventana)
    sys.exit(app.exec())
