import re
import unicodedata


def _normalizar_texto(valor):
    texto = unicodedata.normalize("NFKD", str(valor)).casefold()
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    return re.sub(r"[^\w]", "", texto)


def filtrar_filas_tabla(tabla, texto, columnas=None):
    """Muestra solo las filas que contienen el texto en las columnas indicadas."""
    busqueda = _normalizar_texto(texto)
    columnas = range(tabla.columnCount()) if columnas is None else columnas

    for fila in range(tabla.rowCount()):
        coincide = not busqueda or any(
            busqueda in _normalizar_texto(item.text())
            for columna in columnas
            if (item := tabla.item(fila, columna)) is not None
        )
        tabla.setRowHidden(fila, not coincide)
        if not coincide and tabla.currentRow() == fila:
            tabla.clearSelection()
            tabla.setCurrentItem(None)
