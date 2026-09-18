import re
import unicodedata

from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtWidgets import QTableWidgetItem


SORT_ROLE = Qt.UserRole + 1000
SEARCH_ROLE = Qt.UserRole + 1001


def _normalizar_texto(valor):
    texto = unicodedata.normalize("NFKD", str(valor)).casefold()
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    return re.sub(r"[^\w]", "", texto)


def _normalizar_valor_orden(valor):
    if valor is None:
        return ""
    if isinstance(valor, str):
        return _normalizar_texto(valor)
    return valor


class SortableTableWidgetItem(QTableWidgetItem):
    def __lt__(self, other):
        propio = self.data(SORT_ROLE)
        ajeno = other.data(SORT_ROLE) if other is not None else None

        if propio is not None or ajeno is not None:
            return _clave_orden(propio) < _clave_orden(ajeno)

        return _normalizar_texto(self.text()) < _normalizar_texto(other.text())


def create_sortable_item(display_text, *, sort_value=None, search_value=None):
    item = SortableTableWidgetItem(str(display_text))
    item.setData(SORT_ROLE, _normalizar_valor_orden(display_text if sort_value is None else sort_value))
    item.setData(SEARCH_ROLE, _normalizar_texto(display_text if search_value is None else search_value))
    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
    return item


def _texto_busqueda_item(item):
    valor = item.data(SEARCH_ROLE)
    if valor is not None:
        return str(valor)
    return _normalizar_texto(item.text())


def filtrar_filas_tabla(tabla, texto, columnas=None, *, protected_rows=None, action_columns=None):
    """Muestra solo las filas que contienen el texto en las columnas indicadas."""
    busqueda = _normalizar_texto(texto)
    protected_rows = set(protected_rows or ())
    action_columns = set(action_columns or ())
    columnas = range(tabla.columnCount()) if columnas is None else columnas
    columnas = [columna for columna in columnas if columna not in action_columns]

    for fila in range(tabla.rowCount()):
        if fila in protected_rows:
            tabla.setRowHidden(fila, False)
            continue

        coincide = not busqueda or any(
            busqueda in _texto_busqueda_item(item)
            for columna in columnas
            if (item := tabla.item(fila, columna)) is not None
        )
        tabla.setRowHidden(fila, not coincide)
        if not coincide and tabla.currentRow() == fila:
            tabla.clearSelection()
            tabla.setCurrentItem(None)


def _clave_orden(valor):
    if valor is None:
        return (3, "")
    if isinstance(valor, (int, float)):
        return (0, valor)
    if hasattr(valor, "isoformat"):
        return (1, valor.isoformat())
    return (2, _normalizar_valor_orden(valor))


def _extraer_fila(tabla, fila, action_columns):
    widgets = {}
    items = [tabla.takeItem(fila, columna) for columna in range(tabla.columnCount())]
    for columna in action_columns:
        widget = tabla.cellWidget(fila, columna)
        if widget is not None:
            widgets[columna] = widget
            tabla.removeCellWidget(fila, columna)
            QCoreApplication.removePostedEvents(widget, QEvent.DeferredDelete)
            widget.setParent(None)
    return {"items": items, "widgets": widgets}


def _restaurar_fila(tabla, fila, contenido):
    for columna, item in enumerate(contenido["items"]):
        if item is not None:
            tabla.setItem(fila, columna, item)
    for columna, widget in contenido["widgets"].items():
        tabla.setCellWidget(fila, columna, widget)


def sort_table_preserving_rows(tabla, *, column, order=Qt.AscendingOrder, protected_rows=None, action_columns=None):
    protected_rows = set(protected_rows or ())
    action_columns = set(action_columns or ())
    filas = list(range(tabla.rowCount()))
    contenidos = {fila: _extraer_fila(tabla, fila, action_columns) for fila in filas}
    filas_datos = [fila for fila in filas if fila not in protected_rows]

    def clave_fila(fila):
        item = contenidos[fila]["items"][column] if 0 <= column < tabla.columnCount() else None
        if item is None:
            return _clave_orden(None)
        valor = item.data(SORT_ROLE)
        return _clave_orden(valor if valor is not None else item.text())

    filas_ordenadas = sorted(
        filas_datos,
        key=clave_fila,
        reverse=order == Qt.DescendingOrder,
    )
    destinos_datos = iter(filas_ordenadas)

    for fila in filas:
        origen = fila if fila in protected_rows else next(destinos_datos)
        _restaurar_fila(tabla, fila, contenidos[origen])


def sort_table_from_header_click(tabla, columna, *, protected_rows=None, action_columns=None):
    orden_anterior = getattr(tabla, "_table_filters_sort_order", Qt.DescendingOrder)
    columna_anterior = getattr(tabla, "_table_filters_sort_column", None)
    orden = Qt.DescendingOrder if columna_anterior == columna and orden_anterior == Qt.AscendingOrder else Qt.AscendingOrder

    tabla._table_filters_sort_column = columna
    tabla._table_filters_sort_order = orden
    tabla.horizontalHeader().setSortIndicator(columna, orden)
    sort_table_preserving_rows(
        tabla,
        column=columna,
        order=orden,
        protected_rows=protected_rows,
        action_columns=action_columns,
    )
