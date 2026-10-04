"""Protección del cierre diario en Desktop."""

from utils.api_client import ApiClientError, crear_cierre as crear_cierre_api
from utils.db import db_cursor
from utils.pdf import generar_pdf_cierre
from controllers.accounting_contracts import build_accounting_summary
from controllers.operaciones_servicio_controller import (
    marcar_lavados_solos_cerrados,
    obtener_lavados_solos_pendientes_cierre,
)


def _datos_pdf_cierre(cierre):
    return {
        "Fecha de inicio": cierre.get("fecha_inicio", ""),
        "Fecha de cierre": cierre.get("fecha_cierre", ""),
        "Total recaudado vehículos": f"${cierre.get('total_recaudado', 0)}",
        "Total baños registrados": cierre.get("total_banos", 0),
        "Total recaudado baños": f"${cierre.get('total_banos_monto', 0)}",
        "Lavados solos registrados": cierre.get("total_lavados_solos", 0),
        "Total recaudado lavados solos": f"${cierre.get('total_lavados_solos_monto', 0)}",
        "Mensualidades cobradas": cierre.get("total_mensualidades", 0),
        "Total recaudado mensualidades": f"${cierre.get('total_mensualidades_monto', 0)}",
        "Noches prepagadas cobradas": cierre.get("total_noches", 0),
        "Total recaudado noches prepagadas": f"${cierre.get('total_noches_monto', 0)}",
        "Total ingresos": cierre.get("total_ingresos", 0),
        "Total salidas": cierre.get("total_salidas", 0),
        "Total general bruto": f"${cierre.get('total_general', 0)}",
        "Total gastos": f"${cierre.get('total_gastos', 0)}",
        "Total neto del día": f"${cierre.get('total_neto', 0)}",
        "Registrado por": cierre.get("usuario", ""),
    }


def _fusionar_cierre_con_lavados_solos(cierre, lavados_solos):
    resumen_lavados = build_accounting_summary([], [], lavados_solos)
    actualizado = dict(cierre)
    monto_lavados = int(resumen_lavados["total_lavados_solos_monto"])
    cantidad_lavados = int(resumen_lavados["total_lavados_solos"])
    total_gastos = int(actualizado.get("total_gastos") or 0)
    total_general_base = actualizado.get("total_general")
    if total_general_base is None:
        total_general_base = (
            int(actualizado.get("total_recaudado") or 0)
            + int(actualizado.get("total_banos_monto") or 0)
            + int(actualizado.get("total_lavados_solos_monto") or 0)
            + int(actualizado.get("total_mensualidades_monto") or 0)
            + int(actualizado.get("total_noches_monto") or 0)
        )

    actualizado["total_lavados_solos"] = int(actualizado.get("total_lavados_solos") or 0) + cantidad_lavados
    actualizado["total_lavados_solos_monto"] = int(actualizado.get("total_lavados_solos_monto") or 0) + monto_lavados
    actualizado["total_general"] = int(total_general_base or 0) + monto_lavados
    actualizado["total_neto"] = int(actualizado.get("total_general") or 0) - total_gastos
    return actualizado


def _persistir_cierre_local_con_lavados(cierre):
    with db_cursor(dictionary=True, commit=True) as cursor:
        lavados_solos = obtener_lavados_solos_pendientes_cierre(cursor)
        cierre_actualizado = _fusionar_cierre_con_lavados_solos(cierre, lavados_solos)
        cursor.execute("""
            INSERT INTO cierres_diarios (
                fecha_inicio, fecha_cierre, total_recaudado, total_ingresos,
                total_salidas, total_banos, total_banos_monto,
                total_lavados_solos, total_lavados_solos_monto,
                total_mensualidades, total_mensualidades_monto,
                total_noches, total_noches_monto, total_general,
                total_gastos, total_neto, usuario
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            cierre_actualizado.get("fecha_inicio"),
            cierre_actualizado.get("fecha_cierre"),
            int(cierre_actualizado.get("total_recaudado") or 0),
            int(cierre_actualizado.get("total_ingresos") or 0),
            int(cierre_actualizado.get("total_salidas") or 0),
            int(cierre_actualizado.get("total_banos") or 0),
            int(cierre_actualizado.get("total_banos_monto") or 0),
            int(cierre_actualizado.get("total_lavados_solos") or 0),
            int(cierre_actualizado.get("total_lavados_solos_monto") or 0),
            int(cierre_actualizado.get("total_mensualidades") or 0),
            int(cierre_actualizado.get("total_mensualidades_monto") or 0),
            int(cierre_actualizado.get("total_noches") or 0),
            int(cierre_actualizado.get("total_noches_monto") or 0),
            int(cierre_actualizado.get("total_general") or 0),
            int(cierre_actualizado.get("total_gastos") or 0),
            int(cierre_actualizado.get("total_neto") or 0),
            cierre_actualizado.get("usuario") or "sistema",
        ))
        id_cierre = cursor.lastrowid
        marcar_lavados_solos_cerrados(
            cursor,
            [lavado["id_operacion_servicio"] for lavado in lavados_solos],
            id_cierre,
        )
        return cierre_actualizado


def realizar_cierre_diario(token, api_warning=None):
    """Solicita el cierre a la API, única autoridad para cerrar operaciones."""
    if not token:
        if api_warning:
            return False, api_warning
        return False, "No hay una sesión válida con la API. Inicie sesión nuevamente."

    try:
        cierre = crear_cierre_api(token)
    except ApiClientError as exc:
        if exc.status == 409 and "DAILY_CLOSE_IN_PROGRESS" in (exc.detail or ""):
            return False, "Hay otro cierre diario en curso. Intente nuevamente cuando finalice."
        if exc.status == 409 and "NO_PENDING_CLOSURE" in (exc.detail or ""):
            return False, "No hay registros pendientes para cerrar."
        if exc.status in (401, 403):
            return False, "La sesión con la API no es válida o venció. Inicie sesión nuevamente."
        if exc.detail in ("API_UNAVAILABLE", "API_NOT_CONFIGURED"):
            return False, "No se pudo conectar con la API. Verifique que el servicio esté disponible e inténtelo nuevamente."
        return False, "La API no pudo realizar el cierre. Inténtelo nuevamente."

    try:
        cierre = _persistir_cierre_local_con_lavados(cierre)
    except Exception as exc:
        print(f"[WARN] No se pudo persistir referencia local del cierre: {exc}")

    try:
        generar_pdf_cierre("diario", _datos_pdf_cierre(cierre))
    except Exception:
        return True, (
            f"Cierre realizado con éxito. Total neto: ${cierre.get('total_neto', 0)}. "
            "No se pudo generar el PDF del cierre."
        )
    return True, f"Cierre realizado con éxito. Total neto: ${cierre.get('total_neto', 0)}"

