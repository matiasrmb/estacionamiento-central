from views.login import LoginWindow
from PySide6.QtWidgets import QApplication
import sys


if __name__ == "__main__":
    app = QApplication(sys.argv)
    with open("styles/estilos.qss", "r") as f:
        app.setStyleSheet(f.read())
    ventana = LoginWindow()
    ventana.show()
    sys.exit(app.exec())
