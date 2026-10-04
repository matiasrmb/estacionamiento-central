"""
Controlador para la gestión de reportes de ingresos y salidas de vehículos.

Este módulo permite:
- Consultar los registros de ingresos y salidas dentro de un rango de fechas.
- Filtrar por patente si se requiere.
- Exportar los resultados a un archivo PDF con resumen del total recaudado.
"""

from utils.db import db_cursor
from utils.pdf_utils import ReportePDF, abrir_pdf
from datetime import datetime, time
from fpdf import FPDF
import os
from controllers.accounting_contracts import build_report_totals
from controllers.operaciones_servicio_controller import asegurar_schema_operaciones_servicio_cierre
from utils.api_client import (
    ApiClientError,
    obtener_catalogo_metricas_reporting as obtener_catalogo_metricas_reporting_api,
    obtener_dashboard_reporting as obtener_dashboard_reporting_api,
)


CATEGORY_LABELS = {
    "vehiculo": "Vehículo",
    "bano": "Baño",
    "lavado_solo": "Lavado solo",
    "mensualidad": "Mensualidad",
    "noche": "Noche",
    "gasto": "Gasto",
}


class ReportPayload(dict):
    """Structured report payload with legacy list-like access for old callers."""

    def __len__(self):
        return len(dict.__getitem__(self, "items"))

    def __iter__(self):
        return (_legacy_item(item) for item in dict.__getitem__(self, "items"))

    def __getitem__(self, key):
        if isinstance(key, int):
            return dict.__getitem__(self, "items")[key]
        return dict.__getitem__(self, key)

    def __eq__(self, other):
        if isinstance(other, list):
            return dict.__getitem__(self, "items") == other
        return dict.__eq__(self, other)


MOVIMIENTO_FILTROS = {"todos", "ingresos", "salidas"}


def obtener_resumen_dashboard_reportes(
    fecha_inicio=None,
    fecha_fin=None,
    token=None,
    period_id="current",
    state="open",
):
    if token:
        try:
            catalog = obtener_catalogo_metricas_reporting_api(token)
            dashboard = obtener_dashboard_reporting_api(token, period_id=period_id, state=state)
            return _normalizar_dashboard_reporting_api(catalog, dashboard)
        except ApiClientError as exc:
            if not fecha_inicio or not fecha_fin:
                raise
            local_payload = obtener_reportes(fecha_inicio, fecha_fin)
            local_payload["api_error"] = exc.detail
            return _agregar_metadata_fallback_local(local_payload, exc.detail)

    if not fecha_inicio or not fecha_fin:
        raise ApiClientError(detail="API_NOT_CONFIGURED")

    if state == "closed":
        return obtener_reporte_cierre_local(period_id)

    local_payload = obtener_reportes(fecha_inicio, fecha_fin)
    local_payload["source"] = "local"
    local_payload["source_state"] = "local"
    local_payload["period_state"] = "open"
    local_payload["completeness"] = {"state": "complete", "reason": None}
    local_payload["capacity"] = None
    local_payload["catalog_version"] = None
    return local_payload


def obtener_reporte_cierre_local(period_id):
    id_cierre = _normalizar_period_id_cierre(period_id)
    with db_cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT id_cierre, fecha_inicio, fecha_cierre, total_recaudado,
                   total_ingresos, total_salidas, total_banos, total_banos_monto,
                   total_lavados_solos, total_lavados_solos_monto,
                   total_mensualidades, total_mensualidades_monto,
                   total_noches, total_noches_monto, total_general,
                   total_gastos, total_neto, usuario
            FROM cierres_diarios
            WHERE id_cierre = %s
            LIMIT 1
        """, (id_cierre,))
        cierre = cursor.fetchone()

    if not cierre:
        raise ValueError("Cierre local no encontrado.")

    totals = _totales_desde_cierre(cierre)
    items = _items_desde_cierre(cierre)
    return ReportPayload({
        "source": "local",
        "source_state": "closure",
        "period_state": "closed",
        "period": {
            "id": str(cierre["id_cierre"]),
            "state": "closed",
            "fecha_inicio": cierre.get("fecha_inicio"),
            "fecha_cierre": cierre.get("fecha_cierre"),
        },
        "items": items,
        "totals": totals,
        "completeness": {"state": "complete", "reason": None},
        "capacity": None,
        "catalog_version": None,
    })


def _normalizar_period_id_cierre(period_id):
    if isinstance(period_id, str) and period_id.startswith("closure:"):
        period_id = period_id.split(":", 1)[1]
    return int(period_id)


def _totales_desde_cierre(cierre):
    return {
        "total_recaudado": int(cierre.get("total_recaudado") or 0),
        "total_movimientos": int(cierre.get("total_salidas") or 0),
        "total_banos": int(cierre.get("total_banos") or 0),
        "total_banos_monto": int(cierre.get("total_banos_monto") or 0),
        "total_lavados_solos": int(cierre.get("total_lavados_solos") or 0),
        "total_lavados_solos_monto": int(cierre.get("total_lavados_solos_monto") or 0),
        "total_mensualidades": int(cierre.get("total_mensualidades") or 0),
        "total_mensualidades_monto": int(cierre.get("total_mensualidades_monto") or 0),
        "total_noches": int(cierre.get("total_noches") or 0),
        "total_noches_monto": int(cierre.get("total_noches_monto") or 0),
        "total_gastos": int(cierre.get("total_gastos") or 0),
        "total_general": int(cierre.get("total_general") or 0),
        "total_neto": int(cierre.get("total_neto") or 0),
    }


def _items_desde_cierre(cierre):
    items = []
    if int(cierre.get("total_lavados_solos") or 0):
        items.append({
            "tipo": "lavado_solo",
            "categoria": CATEGORY_LABELS["lavado_solo"],
            "patente": "[LAVADOS CIERRE]",
            "fecha_hora_ingreso": cierre.get("fecha_inicio"),
            "fecha_hora_salida": cierre.get("fecha_cierre"),
            "minutos": 0,
            "tarifa_aplicada": int(cierre.get("total_lavados_solos_monto") or 0),
            "usuario": cierre.get("usuario"),
        })
    return items


def _normalizar_dashboard_reporting_api(catalog, dashboard):
    metrics = dashboard.get("metrics", {})
    catalog_metrics = catalog.get("metrics", [])
    period = dashboard.get("period", {}) or {}
    return {
        "source": "api",
        "source_state": dashboard.get("source_state") or dashboard.get("source") or "api",
        "period": period,
        "period_state": dashboard.get("period_state") or period.get("state") or "open",
        "completeness": dashboard.get("completeness") or {"state": "complete", "reason": None},
        "capacity": dashboard.get("capacity"),
        "catalog_version": dashboard.get("catalog_version") or catalog.get("version"),
        "filters": dashboard.get("filters", {}),
        "pagination": dashboard.get("pagination", {}),
        "summary": [
            {
                "metric": metric["name"],
                "label": metric.get("label") or metric.get("meaning") or metric["name"],
                "sign": metric.get("sign"),
                "value": metrics.get(metric["name"], 0),
            }
            for metric in catalog_metrics
            if metric.get("name") in metrics
        ],
    }


def _agregar_metadata_fallback_local(local_payload, api_error):
    local_payload["source"] = "local_fallback"
    local_payload["source_state"] = "local_fallback"
    local_payload["period_state"] = "open"
    local_payload["completeness"] = {
        "state": "incomplete",
        "reason": f"Reporting API unavailable; local fallback totals may be incomplete ({api_error}).",
    }
    local_payload["capacity"] = None
    local_payload["catalog_version"] = None
    return local_payload


def obtener_reportes(fecha_inicio, fecha_fin, patente="", hora_inicio=None, hora_fin=None, usuario="", movimiento="todos"):
    """
    Obtiene los registros de ingresos y salidas de vehículos dentro de un rango de fechas.

    Args:
        fecha_inicio (date): Fecha inicial del rango a consultar.
        fecha_fin (date): Fecha final del rango a consultar.
        patente (str, opcional): Patente del vehículo para filtrar resultados. Por defecto, devuelve todos.

    Returns:
        dict: Payload con items normalizados y totales contables.
    """
    movimiento = (movimiento or "todos").strip().lower()
    if movimiento not in MOVIMIENTO_FILTROS:
        raise ValueError("Filtro de movimiento inválido.")

    fecha_columna = "i.fecha_hora_ingreso" if movimiento == "ingresos" else "i.fecha_hora_salida"
    salida_requerida = "" if movimiento == "ingresos" else "i.fecha_hora_salida IS NOT NULL AND"
    fecha_condicion = f"DATE({fecha_columna}) BETWEEN %s AND %s"
    params = [fecha_inicio, fecha_fin]

    if movimiento == "todos":
        salida_requerida = ""
        fecha_condicion = """
          (
              (i.fecha_hora_salida IS NOT NULL AND DATE(i.fecha_hora_salida) BETWEEN %s AND %s)
              OR (i.fecha_hora_salida IS NULL AND DATE(i.fecha_hora_ingreso) BETWEEN %s AND %s)
          )
        """
        params = [fecha_inicio, fecha_fin, fecha_inicio, fecha_fin]

    query = f"""
        SELECT 
            v.patente,
            i.fecha_hora_ingreso,
            i.fecha_hora_salida,
            TIMESTAMPDIFF(MINUTE, i.fecha_hora_ingreso, i.fecha_hora_salida) AS minutos,
            i.tarifa_aplicada,
            i.usuario
        FROM ingresos i
        JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
        WHERE {salida_requerida}
          NOT EXISTS (
               SELECT 1 FROM ingresos_eliminados ie
               WHERE ie.id_ingreso_original = i.id_ingreso
           )
          AND {fecha_condicion}
    """

    if patente:
        query += " AND v.patente = %s"
        params.append(patente)
    if hora_inicio:
        if movimiento == "todos":
            query += """
              AND (
                  (i.fecha_hora_salida IS NOT NULL AND TIME(i.fecha_hora_salida) >= %s)
                  OR (i.fecha_hora_salida IS NULL AND TIME(i.fecha_hora_ingreso) >= %s)
              )
            """
            params.extend([hora_inicio, hora_inicio])
        else:
            query += f" AND TIME({fecha_columna}) >= %s"
            params.append(hora_inicio)
    if hora_fin:
        if movimiento == "todos":
            query += """
              AND (
                  (i.fecha_hora_salida IS NOT NULL AND TIME(i.fecha_hora_salida) <= %s)
                  OR (i.fecha_hora_salida IS NULL AND TIME(i.fecha_hora_ingreso) <= %s)
              )
            """
            params.extend([hora_fin, hora_fin])
        else:
            query += f" AND TIME({fecha_columna}) <= %s"
            params.append(hora_fin)
    if usuario:
        query += " AND i.usuario = %s"
        params.append(usuario)

    with db_cursor(dictionary=True) as cursor:
        cursor.execute(query, tuple(params))
        movimientos = cursor.fetchall()
        resultados = [_normalizar_vehiculo(row) for row in movimientos]

        if movimiento != "todos":
            resultados.sort(key=lambda item: item.get("fecha_hora_salida") or item["fecha_hora_ingreso"])
            return ReportPayload({
                "items": resultados,
                "totals": build_report_totals(resultados),
            })

        # Usos de baños (solo si no se filtró patente)
        if not patente:
            asegurar_schema_operaciones_servicio_cierre(cursor)
            cursor.execute("""
                SELECT fecha_hora, monto, usuario
                FROM usos_bano
                WHERE DATE(fecha_hora) BETWEEN %s AND %s
            """ + _time_user_clause("fecha_hora", "usuario", hora_inicio, hora_fin, usuario),
                tuple([fecha_inicio, fecha_fin] + _time_user_params(hora_inicio, hora_fin, usuario))
            )
            banos = cursor.fetchall()
            for b in banos:
                resultados.append(_normalizar_bano(b))

            cursor.execute("""
                SELECT patente, fecha_hora_inicio, fecha_hora_fin,
                       TIMESTAMPDIFF(MINUTE, fecha_hora_inicio, fecha_hora_fin) AS minutos,
                       valor_lavado_snapshot, usuario_fin
                FROM operaciones_servicio
                WHERE estado = 'FINALIZADO_COBRADO'
                  AND cerrado = FALSE
                  AND id_cierre IS NULL
                  AND id_ingreso_generado IS NULL
                  AND fecha_hora_fin IS NOT NULL
                  AND DATE(fecha_hora_fin) BETWEEN %s AND %s
            """ + _time_user_clause("fecha_hora_fin", "usuario_fin", hora_inicio, hora_fin, usuario) + """
                ORDER BY fecha_hora_fin
            """, tuple([fecha_inicio, fecha_fin] + _time_user_params(hora_inicio, hora_fin, usuario)))
            lavados = cursor.fetchall()
            for lavado in lavados:
                resultados.append(_normalizar_lavado(lavado))

            cursor.execute("""
                SELECT fecha_hora, monto, descripcion, usuario
                FROM gastos_operacion
                WHERE DATE(fecha_hora) BETWEEN %s AND %s
            """ + _time_user_clause("fecha_hora", "usuario", hora_inicio, hora_fin, usuario) + """
                ORDER BY fecha_hora
            """, tuple([fecha_inicio, fecha_fin] + _time_user_params(hora_inicio, hora_fin, usuario)))
            gastos = cursor.fetchall()
            for gasto in gastos:
                resultados.append(_normalizar_gasto(gasto))
        else:
            asegurar_schema_operaciones_servicio_cierre(cursor)
            cursor.execute("""
                SELECT patente, fecha_hora_inicio, fecha_hora_fin,
                       TIMESTAMPDIFF(MINUTE, fecha_hora_inicio, fecha_hora_fin) AS minutos,
                       valor_lavado_snapshot, usuario_fin
                FROM operaciones_servicio
                WHERE patente = %s
                  AND estado = 'FINALIZADO_COBRADO'
                  AND cerrado = FALSE
                  AND id_cierre IS NULL
                  AND id_ingreso_generado IS NULL
                  AND fecha_hora_fin IS NOT NULL
                  AND DATE(fecha_hora_fin) BETWEEN %s AND %s
            """ + _time_user_clause("fecha_hora_fin", "usuario_fin", hora_inicio, hora_fin, usuario) + """
                ORDER BY fecha_hora_fin
            """, tuple([patente, fecha_inicio, fecha_fin] + _time_user_params(hora_inicio, hora_fin, usuario)))
            lavados = cursor.fetchall()
            for lavado in lavados:
                resultados.append(_normalizar_lavado(lavado))

        pagos_query = """
            SELECT v.patente, p.periodo, p.fecha_pago, p.monto_snapshot, p.usuario
            FROM pagos_mensuales p
            JOIN vehiculos v ON p.id_vehiculo = v.id_vehiculo
            WHERE DATE(p.fecha_pago) BETWEEN %s AND %s
        """
        pagos_params = [fecha_inicio, fecha_fin]
        if patente:
            pagos_query += " AND v.patente = %s"
            pagos_params.append(patente)
        if hora_inicio:
            pagos_query += " AND TIME(p.fecha_pago) >= %s"
            pagos_params.append(hora_inicio)
        if hora_fin:
            pagos_query += " AND TIME(p.fecha_pago) <= %s"
            pagos_params.append(hora_fin)
        if usuario:
            pagos_query += " AND p.usuario = %s"
            pagos_params.append(usuario)
        pagos_query += " ORDER BY p.fecha_pago"
        cursor.execute(pagos_query, tuple(pagos_params))
        pagos = cursor.fetchall()
        for pago in pagos:
            resultados.append(_normalizar_mensualidad(pago))

        noches_query = """
            SELECT v.patente, c.fecha_hora_pago, c.monto_snapshot, c.usuario
            FROM cobros_noches c
            JOIN ingresos i ON i.id_ingreso = c.id_ingreso
            JOIN vehiculos v ON v.id_vehiculo = i.id_vehiculo
            WHERE c.estado = 'PAGADO'
              AND NOT EXISTS (
                  SELECT 1 FROM ingresos_eliminados ie
                  WHERE ie.id_ingreso_original = i.id_ingreso
              )
              AND DATE(c.fecha_hora_pago) BETWEEN %s AND %s
        """
        noches_params = [fecha_inicio, fecha_fin]
        if patente:
            noches_query += " AND v.patente = %s"
            noches_params.append(patente)
        if hora_inicio:
            noches_query += " AND TIME(c.fecha_hora_pago) >= %s"
            noches_params.append(hora_inicio)
        if hora_fin:
            noches_query += " AND TIME(c.fecha_hora_pago) <= %s"
            noches_params.append(hora_fin)
        if usuario:
            noches_query += " AND c.usuario = %s"
            noches_params.append(usuario)
        noches_query += " ORDER BY c.fecha_hora_pago, c.id_cobro_noche"
        cursor.execute(noches_query, tuple(noches_params))
        noches = cursor.fetchall()
        for cobro in noches:
            resultados.append(_normalizar_noche(cobro))

    resultados.sort(key=lambda item: item.get("fecha_hora_salida") or item["fecha_hora_ingreso"])
    return ReportPayload({
        "items": resultados,
        "totals": build_report_totals(resultados),
    })


def _time_user_clause(event_column, user_column, hora_inicio=None, hora_fin=None, usuario=""):
    clause = ""
    if hora_inicio:
        clause += f" AND TIME({event_column}) >= %s"
    if hora_fin:
        clause += f" AND TIME({event_column}) <= %s"
    if usuario:
        clause += f" AND {user_column} = %s"
    return clause


def _time_user_params(hora_inicio=None, hora_fin=None, usuario=""):
    params = []
    if hora_inicio:
        params.append(hora_inicio)
    if hora_fin:
        params.append(hora_fin)
    if usuario:
        params.append(usuario)
    return params


def _legacy_item(item):
    legacy = dict(item)
    if legacy.get("tipo") == "mensualidad":
        legacy["patente"] = f"[MENSUAL] {legacy['patente']}"
    elif legacy.get("tipo") == "noche":
        legacy["patente"] = f"[NOCHES] {legacy['patente']}"
    return legacy


def _normalizar_vehiculo(row):
    return {
        "tipo": "vehiculo",
        "categoria": CATEGORY_LABELS["vehiculo"],
        "patente": row["patente"],
        "fecha_hora_ingreso": row["fecha_hora_ingreso"],
        "fecha_hora_salida": row["fecha_hora_salida"],
        "minutos": row.get("minutos"),
        "tarifa_aplicada": row.get("tarifa_aplicada"),
        "usuario": row.get("usuario"),
    }


def _normalizar_bano(row):
    return {
        "tipo": "bano",
        "categoria": CATEGORY_LABELS["bano"],
        "patente": "[BAÑO]",
        "fecha_hora_ingreso": row["fecha_hora"],
        "fecha_hora_salida": row["fecha_hora"],
        "minutos": 0,
        "tarifa_aplicada": row.get("monto") or 0,
        "usuario": row.get("usuario"),
    }


def _normalizar_lavado(row):
    return {
        "tipo": "lavado_solo",
        "categoria": CATEGORY_LABELS["lavado_solo"],
        "patente": row["patente"],
        "fecha_hora_ingreso": row["fecha_hora_inicio"],
        "fecha_hora_salida": row["fecha_hora_fin"],
        "minutos": row.get("minutos") or 0,
        "tarifa_aplicada": row.get("valor_lavado_snapshot") or 0,
        "usuario": row.get("usuario_fin") or row.get("usuario"),
    }


def _normalizar_gasto(row):
    return {
        "tipo": "gasto",
        "categoria": CATEGORY_LABELS["gasto"],
        "patente": "[GASTO]",
        "fecha_hora_ingreso": row["fecha_hora"],
        "fecha_hora_salida": row["fecha_hora"],
        "minutos": 0,
        "tarifa_aplicada": -(row.get("monto") or 0),
        "usuario": row.get("usuario"),
    }


def _normalizar_mensualidad(row):
    return {
        "tipo": "mensualidad",
        "categoria": CATEGORY_LABELS["mensualidad"],
        "patente": row["patente"],
        "fecha_hora_ingreso": row["fecha_pago"],
        "fecha_hora_salida": row["fecha_pago"],
        "minutos": 0,
        "tarifa_aplicada": row.get("monto_snapshot") or 0,
        "usuario": row.get("usuario"),
    }


def _normalizar_noche(row):
    return {
        "tipo": "noche",
        "categoria": CATEGORY_LABELS["noche"],
        "patente": row["patente"],
        "fecha_hora_ingreso": row["fecha_hora_pago"],
        "fecha_hora_salida": row["fecha_hora_pago"],
        "minutos": 0,
        "tarifa_aplicada": row.get("monto_snapshot") or 0,
        "usuario": row.get("usuario"),
    }

def exportar_pdf(datos, fecha_inicio=None, fecha_fin=None, incluir_banos=False, patente=""):
    """
    Exporta los resultados de los reportes a un archivo PDF con formato estandarizado.

    El archivo se guarda en la carpeta `reportes` con un nombre que incluye el rango de fechas o timestamp.

    Args:
        datos (list[dict]): Lista de movimientos obtenidos con `obtener_reportes`.
        fecha_inicio (date, opcional): Fecha inicial del filtro (para el nombre del archivo).
        fecha_fin (date, opcional): Fecha final del filtro (para el nombre del archivo).
    """
    pdf = ReportePDF("Reporte de Ingresos y Salidas")
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    if isinstance(datos, dict) and "items" in datos:
        items = datos.get("items") or []
        totals = datos.get("totals") or build_report_totals(items)
    else:
        items = datos
        totals = None

    total = 0
    total_banos = totals.get("total_banos", 0) if totals else 0
    monto_banos = totals.get("total_banos_monto", 0) if totals else 0
    total_lavados = totals.get("total_lavados_solos", 0) if totals else len([row for row in items if row.get("tipo") == "lavado_solo"])
    monto_lavados = totals.get("total_lavados_solos_monto", 0) if totals else sum(row.get("tarifa_aplicada") or 0 for row in items if row.get("tipo") == "lavado_solo")
    total_mensualidades = totals.get("total_mensualidades", 0) if totals else 0
    monto_mensualidades = totals.get("total_mensualidades_monto", 0) if totals else 0
    total_noches = totals.get("total_noches", 0) if totals else 0
    monto_noches = totals.get("total_noches_monto", 0) if totals else 0

    if totals is None and fecha_inicio and fecha_fin:
        with db_cursor(dictionary=True) as cursor:
            if incluir_banos:
                cursor.execute("""
                    SELECT COUNT(*) AS cantidad, SUM(monto) AS total
                    FROM usos_bano
                    WHERE DATE(fecha_hora) BETWEEN %s AND %s
                """, (fecha_inicio, fecha_fin))
                resultado = cursor.fetchone()
                total_banos = resultado["cantidad"] or 0
                monto_banos = resultado["total"] or 0

            pagos_query = """
                SELECT COUNT(*) AS cantidad, SUM(p.monto_snapshot) AS total
                FROM pagos_mensuales p
                JOIN vehiculos v ON p.id_vehiculo = v.id_vehiculo
                WHERE DATE(p.fecha_pago) BETWEEN %s AND %s
            """
            pagos_params = [fecha_inicio, fecha_fin]
            if patente:
                pagos_query += " AND v.patente = %s"
                pagos_params.append(patente)
            cursor.execute(pagos_query, tuple(pagos_params))
            resultado_mensualidades = cursor.fetchone()
            total_mensualidades = resultado_mensualidades["cantidad"] or 0
            monto_mensualidades = resultado_mensualidades["total"] or 0

            noches_query = """
                SELECT COUNT(*) AS cantidad, SUM(c.monto_snapshot) AS total
                FROM cobros_noches c
                JOIN ingresos i ON i.id_ingreso = c.id_ingreso
                JOIN vehiculos v ON v.id_vehiculo = i.id_vehiculo
                WHERE c.estado = 'PAGADO'
                  AND NOT EXISTS (
                      SELECT 1 FROM ingresos_eliminados ie
                      WHERE ie.id_ingreso_original = i.id_ingreso
                  )
                  AND DATE(c.fecha_hora_pago) BETWEEN %s AND %s
            """
            noches_params = [fecha_inicio, fecha_fin]
            if patente:
                noches_query += " AND v.patente = %s"
                noches_params.append(patente)
            cursor.execute(noches_query, tuple(noches_params))
            resultado_noches = cursor.fetchone()
            total_noches = resultado_noches["cantidad"] or 0
            monto_noches = resultado_noches["total"] or 0

    for row in items:
        ingreso = row["fecha_hora_ingreso"].strftime("%d-%m-%Y %H:%M")
        salida_valor = row.get("fecha_hora_salida")
        salida = salida_valor.strftime("%d-%m-%Y %H:%M") if salida_valor else "-"
        tarifa = row.get("tarifa_aplicada") or 0
        total += tarifa

        pdf.cell(0, 8, f"{row['patente']} | {ingreso} -> {salida} | ${tarifa:.0f}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    total_neto = totals.get("total_neto", total) if totals else total
    total_general = totals.get("total_general", total) if totals else total
    pdf.cell(0, 10, f"Total neto: ${total_neto:.0f}", ln=True)

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Mensualidades cobradas: {total_mensualidades}", ln=True)
    pdf.cell(0, 8, f"Total recaudado por mensualidades: ${monto_mensualidades:.0f}", ln=True)
    pdf.cell(0, 8, f"Noches prepagadas cobradas: {total_noches}", ln=True)
    pdf.cell(0, 8, f"Total recaudado por Noches prepagadas: ${monto_noches:.0f}", ln=True)

    if incluir_banos:
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 8, f"Baños registrados: {total_banos}", ln=True)
        pdf.cell(0, 8, f"Total recaudado por baños: ${monto_banos:.0f}", ln=True)
        pdf.cell(0, 8, f"Lavados independientes registrados: {total_lavados}", ln=True)
        pdf.cell(0, 8, f"Total por lavados independientes: ${monto_lavados:.0f}", ln=True)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Total bruto (vehículos, baños, lavados, mensualidades y noches): ${total_general:.0f}", ln=True)
        pdf.set_font("Arial", "", 9)
        pdf.cell(0, 6, "Nota: los lavados vinculados a una estadía se incluyen en el importe del vehículo.", ln=True)

    carpeta = "reportes"
    os.makedirs(carpeta, exist_ok=True)
    nombre_archivo = "reporte_ingresos"
    if fecha_inicio and fecha_fin:
        nombre_archivo += f"_{fecha_inicio.strftime('%Y%m%d')}_a_{fecha_fin.strftime('%Y%m%d')}"
    else:
        nombre_archivo += f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    ruta = os.path.join(carpeta, nombre_archivo + ".pdf")

    pdf.output(ruta)
    abrir_pdf(ruta)
