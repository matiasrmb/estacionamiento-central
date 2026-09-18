"""Operaciones de gastos vinculables al cierre diario."""

import json
from datetime import datetime

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


def _exigir_admin(rol):
    if str(rol or "").strip().lower() not in {"admin", "administrador"}:
        raise PermissionError("Solo un administrador puede editar o eliminar gastos.")


def _snapshot(gasto):
    if gasto is None:
        return None
    data = dict(gasto)
    fecha = data.get("fecha_hora")
    if hasattr(fecha, "isoformat"):
        data["fecha_hora"] = fecha.isoformat()
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def registrar_gasto(categoria, descripcion, monto, usuario):
    """Registra un gasto pendiente para el período de cierre actual."""
    categoria = _texto_requerido(categoria, "La categoría")
    descripcion = _texto_requerido(descripcion, "La descripción")
    usuario = _texto_requerido(usuario, "El usuario")
    monto = _monto_positivo(monto)
    fecha_hora = datetime.now()
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
    with db_cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT id_gasto, fecha_hora, categoria, descripcion, monto, usuario, id_cierre
            FROM gastos_operacion
            WHERE id_cierre IS NULL
            ORDER BY fecha_hora DESC, id_gasto DESC
        """)
        return cursor.fetchall()


def editar_gasto(id_gasto, categoria, descripcion, monto, usuario, rol):
    """Edita un gasto pendiente y registra auditoría administrativa."""
    _exigir_admin(rol)
    categoria = _texto_requerido(categoria, "La categoría")
    descripcion = _texto_requerido(descripcion, "La descripción")
    usuario = _texto_requerido(usuario, "El usuario")
    monto = _monto_positivo(monto)

    with db_cursor(dictionary=True, commit=True) as cursor:
        gasto = _obtener_gasto_bloqueado(cursor, id_gasto)
        if gasto is None:
            raise LookupError("Gasto no encontrado.")
        if gasto.get("id_cierre") is not None:
            raise ValueError("No se puede editar un gasto ya asociado a un cierre.")
        _asegurar_auditoria_disponible(cursor)

        nuevo = dict(gasto)
        nuevo.update({"categoria": categoria, "descripcion": descripcion, "monto": monto})
        cursor.execute("""
            UPDATE gastos_operacion
            SET categoria = %s, descripcion = %s, monto = %s
            WHERE id_gasto = %s AND id_cierre IS NULL
        """, (categoria, descripcion, monto, id_gasto))
        _auditar(cursor, id_gasto, "EDITAR", usuario, gasto, nuevo)
        return nuevo


def eliminar_gasto(id_gasto, usuario, rol):
    """Elimina un gasto pendiente y conserva evidencia en auditoría."""
    _exigir_admin(rol)
    usuario = _texto_requerido(usuario, "El usuario")
    with db_cursor(dictionary=True, commit=True) as cursor:
        gasto = _obtener_gasto_bloqueado(cursor, id_gasto)
        if gasto is None:
            raise LookupError("Gasto no encontrado.")
        if gasto.get("id_cierre") is not None:
            raise ValueError("No se puede eliminar un gasto ya asociado a un cierre.")
        _asegurar_auditoria_disponible(cursor)
        cursor.execute("""
            DELETE FROM gastos_operacion
            WHERE id_gasto = %s AND id_cierre IS NULL
        """, (id_gasto,))
        _auditar(cursor, id_gasto, "ELIMINAR", usuario, gasto, None)
        return {"ok": True, "id_gasto": id_gasto}


def _obtener_gasto_bloqueado(cursor, id_gasto):
    cursor.execute("""
        SELECT id_gasto, fecha_hora, categoria, descripcion, monto, usuario, id_cierre
        FROM gastos_operacion
        WHERE id_gasto = %s
        FOR UPDATE
    """, (id_gasto,))
    return cursor.fetchone()


def _asegurar_auditoria_disponible(cursor):
    try:
        cursor.execute("SELECT 1 FROM gastos_operacion_auditoria LIMIT 1")
        cursor.fetchone()
    except Exception as exc:
        raise RuntimeError(
            "Falta aplicar la migración de auditoría de gastos (tabla gastos_operacion_auditoria)."
        ) from exc


def _auditar(cursor, id_gasto, accion, usuario, anterior, nuevo):
    cursor.execute("""
        INSERT INTO gastos_operacion_auditoria (
            id_gasto, accion, usuario, fecha_hora, snapshot_anterior, snapshot_nuevo
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (id_gasto, accion, usuario, datetime.now(), _snapshot(anterior), _snapshot(nuevo)))


def obtener_total_gastos_pendientes():
    """Retorna el total de gastos pendientes para el período actual."""
    with db_cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT COALESCE(SUM(monto), 0) AS total
            FROM gastos_operacion
            WHERE id_cierre IS NULL
        """)
        row = cursor.fetchone() or {}
        return int(row.get("total") or 0)
