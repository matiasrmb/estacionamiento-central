"""Operaciones de gastos vinculables al cierre diario."""

from datetime import datetime

from controllers.cierres_controller import asegurar_schema_cierres
from utils.db import db_cursor


def _texto_requerido(valor, nombre):
    texto = str(valor or "").strip()
    if not texto:
        raise ValueError(f"{nombre} es obligatorio.")
    return texto


def _monto_positivo(monto):
    if isinstance(monto, bool):
        raise ValueError("El monto debe ser un entero positivo.")
    try:
        monto_entero = int(monto)
    except (TypeError, ValueError) as exc:
        raise ValueError("El monto debe ser un entero positivo.") from exc
    if monto_entero <= 0 or str(monto_entero) != str(monto).strip():
        raise ValueError("El monto debe ser un entero positivo.")
    return monto_entero


def registrar_gasto(categoria, descripcion, monto, usuario):
    """Registra un gasto pendiente para el período de cierre actual."""
    categoria = _texto_requerido(categoria, "La categoría")
    descripcion = _texto_requerido(descripcion, "La descripción")
    usuario = _texto_requerido(usuario, "El usuario")
    monto = _monto_positivo(monto)
    fecha_hora = datetime.now()
    asegurar_schema_cierres()

    with db_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO gastos_operacion (
                fecha_hora, categoria, descripcion, monto, usuario
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (fecha_hora, categoria, descripcion, monto, usuario))
        id_gasto = cursor.lastrowid

    return {
        "id_gasto": id_gasto,
        "fecha_hora": fecha_hora,
        "categoria": categoria,
        "descripcion": descripcion,
        "monto": monto,
        "usuario": usuario,
    }


def obtener_gastos_pendientes():
    """Retorna gastos aún no vinculados a un cierre, del más reciente al más antiguo."""
    asegurar_schema_cierres()
    with db_cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT id_gasto, fecha_hora, categoria, descripcion, monto, usuario
            FROM gastos_operacion
            WHERE id_cierre IS NULL
            ORDER BY fecha_hora DESC, id_gasto DESC
        """)
        return cursor.fetchall()


def obtener_total_gastos_pendientes():
    """Retorna el total de gastos pendientes para el período actual."""
    asegurar_schema_cierres()
    with db_cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT COALESCE(SUM(monto), 0) AS total
            FROM gastos_operacion
            WHERE id_cierre IS NULL
        """)
        row = cursor.fetchone() or {}
        return int(row.get("total") or 0)
