from PySide6.QtCore import QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox

from app_version import APP_VERSION
from utils.update_checker import UpdateCheckResult, check_for_update


class UpdateCheckWorker(QThread):
    result_ready = Signal(object)

    def run(self):
        self.result_ready.emit(check_for_update(APP_VERSION))


def schedule_startup_update_check(parent, delay_ms=1000):
    QTimer.singleShot(delay_ms, lambda: start_update_check(parent))


def start_update_check(parent):
    worker = UpdateCheckWorker(parent)
    parent._update_check_worker = worker
    worker.result_ready.connect(lambda result: _show_update_message(parent, result))
    worker.finished.connect(worker.deleteLater)
    worker.start()


def _show_update_message(parent, result: UpdateCheckResult):
    if not result.update_available or not result.release_url:
        return

    message = QMessageBox(parent)
    message.setIcon(QMessageBox.Information)
    message.setWindowTitle("Actualización disponible")
    message.setText(f"Hay una nueva versión disponible: {result.latest_version}")
    message.setInformativeText(
        f"Tu versión actual es {result.current_version}. "
        "Podés abrir la página de descarga para instalarla manualmente."
    )
    download_button = message.addButton("Descargar", QMessageBox.AcceptRole)
    message.addButton("Más tarde", QMessageBox.RejectRole)
    message.exec()

    if message.clickedButton() == download_button:
        QDesktopServices.openUrl(QUrl(result.release_url))
