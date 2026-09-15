"""Protección del cierre diario en Desktop."""

from utils.api_client import ApiClientError, crear_cierre as crear_cierre_api
from utils.pdf import generar_pdf_cierre


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
        generar_pdf_cierre("diario", _datos_pdf_cierre(cierre))
    except Exception:
        return True, (
            f"Cierre realizado con éxito. Total neto: ${cierre.get('total_neto', 0)}. "
            "No se pudo generar el PDF del cierre."
        )
    return True, f"Cierre realizado con éxito. Total neto: ${cierre.get('total_neto', 0)}"

