import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from views.asistencias import AsistenciasWindow
from views.mensuales import MensualesWindow
from views.reportes import ReportesWindow


def completer_values(completer):
    model = completer.model()
    return [model.data(model.index(row, 0)) for row in range(model.rowCount())]


class DesktopAutocompleteViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_reportes_patente_input_uses_known_plate_completer(self):
        with patch("views.reportes.obtener_patentes_conocidas", return_value=["ABC123", "XYZ789"]), \
             patch("views.reportes.obtener_usuarios", return_value=[]):
            view = ReportesWindow()

        completer = view.input_patente.completer()

        self.assertIs(completer, view.completer_patentes)
        self.assertEqual(completer.caseSensitivity(), Qt.CaseInsensitive)
        self.assertEqual(completer.filterMode(), Qt.MatchContains)
        self.assertEqual(completer_values(completer), ["ABC123", "XYZ789"])

    def test_mensuales_patente_input_uses_known_plate_completer(self):
        with patch("views.mensuales.obtener_patentes_conocidas", return_value=["AAA111", "BBB222"]), \
             patch("views.mensuales.obtener_mensuales", return_value=[]):
            view = MensualesWindow(usuario="operador")

        completer = view.patente_input.completer()

        self.assertIs(completer, view.completer_patentes)
        self.assertEqual(completer.caseSensitivity(), Qt.CaseInsensitive)
        self.assertEqual(completer.filterMode(), Qt.MatchContains)
        self.assertEqual(completer_values(completer), ["AAA111", "BBB222"])

    def test_asistencias_usuario_input_uses_user_completer(self):
        usuarios = [{"usuario": "admin"}, {"usuario": "operador"}, {"usuario": ""}]
        with patch("views.asistencias.obtener_usuarios", return_value=usuarios):
            view = AsistenciasWindow()

        completer = view.input_usuario.completer()

        self.assertIs(completer, view.completer_usuarios)
        self.assertEqual(completer.caseSensitivity(), Qt.CaseInsensitive)
        self.assertEqual(completer.filterMode(), Qt.MatchContains)
        self.assertEqual(completer_values(completer), ["admin", "operador"])


if __name__ == "__main__":
    unittest.main()
