import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem

from utils.table_filters import filtrar_filas_tabla


class TableFiltersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_filters_all_visible_columns_case_insensitively_and_normalizes_plates(self):
        tabla = QTableWidget(2, 2)
        tabla.setItem(0, 0, QTableWidgetItem("AB-CD 12"))
        tabla.setItem(0, 1, QTableWidgetItem("Pendiente"))
        tabla.setItem(1, 0, QTableWidgetItem("EFGH34"))
        tabla.setItem(1, 1, QTableWidgetItem("Pagado"))

        filtrar_filas_tabla(tabla, "abcd12")

        self.assertFalse(tabla.isRowHidden(0))
        self.assertTrue(tabla.isRowHidden(1))

    def test_empty_search_shows_all_rows(self):
        tabla = QTableWidget(2, 1)
        for fila, texto in enumerate(("Uno", "Dos")):
            tabla.setItem(fila, 0, QTableWidgetItem(texto))

        filtrar_filas_tabla(tabla, "uno")
        filtrar_filas_tabla(tabla, "")

        self.assertFalse(tabla.isRowHidden(0))
        self.assertFalse(tabla.isRowHidden(1))

    def test_clears_the_current_row_when_the_filter_hides_it(self):
        tabla = QTableWidget(2, 1)
        tabla.setItem(0, 0, QTableWidgetItem("Uno"))
        tabla.setItem(1, 0, QTableWidgetItem("Dos"))
        tabla.setCurrentCell(0, 0)

        filtrar_filas_tabla(tabla, "dos")

        self.assertEqual(tabla.currentRow(), -1)
