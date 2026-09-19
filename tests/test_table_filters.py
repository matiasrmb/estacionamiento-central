import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtWidgets import QApplication, QPushButton, QTableWidget, QTableWidgetItem

from utils.table_filters import filtrar_filas_tabla
import utils.table_filters as table_filters


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


class TypedTableSortingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _item(self, display_text, sort_value):
        return table_filters.create_sortable_item(display_text, sort_value=sort_value)

    def _sorted_column_texts(self, rows, order=Qt.AscendingOrder):
        table = QTableWidget(len(rows), 1)
        for row, (display_text, sort_value) in enumerate(rows):
            table.setItem(row, 0, self._item(display_text, sort_value))

        table.sortItems(0, order)

        return [table.item(row, 0).text() for row in range(table.rowCount())]

    def test_sorts_formatted_money_by_numeric_value(self):
        values = [
            ("$ 12.500", 12500),
            ("$ 900", 900),
            ("$ 2.000", 2000),
        ]

        self.assertEqual(
            self._sorted_column_texts(values),
            ["$ 900", "$ 2.000", "$ 12.500"],
        )

    def test_sorts_dates_and_times_by_datetime_value(self):
        values = [
            ("02/09/2026 08:00", "2026-09-02T08:00:00"),
            ("01/09/2026 20:30", "2026-09-01T20:30:00"),
            ("01/09/2026 09:15", "2026-09-01T09:15:00"),
        ]

        self.assertEqual(
            self._sorted_column_texts(values),
            ["01/09/2026 09:15", "01/09/2026 20:30", "02/09/2026 08:00"],
        )

    def test_sorts_numbers_by_numeric_value_instead_of_display_text(self):
        values = [("10 min", 10), ("2 min", 2), ("45 min", 45)]

        self.assertEqual(
            self._sorted_column_texts(values),
            ["2 min", "10 min", "45 min"],
        )

    def test_sorts_identifiers_by_semantic_id_value(self):
        values = [("#10", 10), ("#2", 2), ("#100", 100)]

        self.assertEqual(
            self._sorted_column_texts(values),
            ["#2", "#10", "#100"],
        )

    def test_sorts_text_by_normalized_value(self):
        values = [("Ñandú", "nandu"), ("Árbol", "arbol"), ("auto", "auto")]

        self.assertEqual(
            self._sorted_column_texts(values),
            ["Árbol", "auto", "Ñandú"],
        )


class ProtectedRowsAndSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _make_table_with_total_row(self):
        table = QTableWidget(3, 2)
        table.setItem(0, 0, table_filters.create_sortable_item("BBB222", sort_value="bbb222"))
        table.setItem(0, 1, table_filters.create_sortable_item("$ 2.000", sort_value=2000))
        table.setItem(1, 0, table_filters.create_sortable_item("AAA111", sort_value="aaa111"))
        table.setItem(1, 1, table_filters.create_sortable_item("$ 1.000", sort_value=1000))
        table.setItem(2, 0, QTableWidgetItem("Total"))
        table.setItem(2, 1, QTableWidgetItem("$ 3.000"))
        return table

    def test_sort_keeps_total_row_outside_sorted_data_rows(self):
        table = self._make_table_with_total_row()

        table_filters.sort_table_preserving_rows(
            table,
            column=0,
            order=Qt.AscendingOrder,
            protected_rows={2},
        )

        self.assertEqual(table.item(0, 0).text(), "AAA111")
        self.assertEqual(table.item(1, 0).text(), "BBB222")
        self.assertEqual(table.item(2, 0).text(), "Total")

    def test_sort_keeps_action_widgets_attached_to_their_records(self):
        table = QTableWidget(2, 3)
        table.setItem(0, 0, table_filters.create_sortable_item("BBB222", sort_value="bbb222"))
        table.setItem(1, 0, table_filters.create_sortable_item("AAA111", sort_value="aaa111"))
        table.setCellWidget(0, 2, QPushButton("Edit BBB222"))
        table.setCellWidget(1, 2, QPushButton("Edit AAA111"))

        table_filters.sort_table_preserving_rows(
            table,
            column=0,
            order=Qt.AscendingOrder,
            action_columns={2},
        )

        self.assertEqual(table.item(0, 0).text(), "AAA111")
        self.assertEqual(table.cellWidget(0, 2).text(), "Edit AAA111")
        self.assertEqual(table.item(1, 0).text(), "BBB222")
        self.assertEqual(table.cellWidget(1, 2).text(), "Edit BBB222")

    def test_search_matches_normalized_text_and_keeps_protected_rows_visible(self):
        table = self._make_table_with_total_row()

        filtrar_filas_tabla(table, "aaa111", columnas=[0], protected_rows={2})

        self.assertTrue(table.isRowHidden(0))
        self.assertFalse(table.isRowHidden(1))
        self.assertFalse(table.isRowHidden(2))

    def test_search_ignores_action_columns_when_matching(self):
        table = QTableWidget(2, 2)
        table.setItem(0, 0, QTableWidgetItem("AAA111"))
        table.setItem(1, 0, QTableWidgetItem("BBB222"))
        table.setCellWidget(0, 1, QPushButton("Delete"))
        table.setCellWidget(1, 1, QPushButton("Delete"))

        filtrar_filas_tabla(table, "delete", columnas=[0, 1], action_columns={1})

        self.assertTrue(table.isRowHidden(0))
        self.assertTrue(table.isRowHidden(1))

    def test_clearing_search_restores_all_eligible_data_rows(self):
        table = self._make_table_with_total_row()

        filtrar_filas_tabla(table, "aaa111", columnas=[0], protected_rows={2})
        filtrar_filas_tabla(table, "", columnas=[0], protected_rows={2})

        self.assertFalse(table.isRowHidden(0))
        self.assertFalse(table.isRowHidden(1))
        self.assertFalse(table.isRowHidden(2))

    def test_header_click_sort_keeps_protected_rows_and_action_widgets_alive(self):
        table = QTableWidget(3, 3)
        table.setHorizontalHeaderLabels(["Plate", "Amount", "Actions"])
        table.setItem(0, 0, table_filters.create_sortable_item("BBB222", sort_value="bbb222"))
        table.setItem(0, 1, table_filters.create_sortable_item("$ 2.000", sort_value=2000))
        table.setCellWidget(0, 2, QPushButton("Edit BBB222"))
        table.setItem(1, 0, table_filters.create_sortable_item("AAA111", sort_value="aaa111"))
        table.setItem(1, 1, table_filters.create_sortable_item("$ 1.000", sort_value=1000))
        table.setCellWidget(1, 2, QPushButton("Edit AAA111"))
        table.setItem(2, 0, QTableWidgetItem("Total"))
        table.setItem(2, 1, QTableWidgetItem("$ 3.000"))

        table.horizontalHeader().setSortIndicatorShown(True)
        table.horizontalHeader().sectionClicked.connect(
            lambda column: table_filters.sort_table_from_header_click(
                table,
                column,
                protected_rows={2},
                action_columns={2},
            )
        )

        table.horizontalHeader().sectionClicked.emit(0)
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.app.processEvents()

        self.assertEqual(table.item(0, 0).text(), "AAA111")
        self.assertEqual(table.cellWidget(0, 2).text(), "Edit AAA111")
        self.assertEqual(table.item(1, 0).text(), "BBB222")
        self.assertEqual(table.cellWidget(1, 2).text(), "Edit BBB222")
        self.assertEqual(table.item(2, 0).text(), "Total")
