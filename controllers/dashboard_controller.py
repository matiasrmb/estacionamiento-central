"""
Controlador del resumen diario del sistema.

Obtiene estadísticas simples para el panel principal (dashboard) del sistema.
"""

from utils.db import db_cursor
from utils.slowlog import slow_operation
from controllers.registro_controller import obtener_resumen_caja_actual, obtener_vehiculos_activos
from controllers.operaciones_servicio_controller import obtener_solo_lavados_activos


def calcular_metricas_panel(caja, vehiculos_activos, solo_lavados_activos, mensualidades_mes):
    """Construye las métricas del panel sin mezclar cobros y proyecciones."""
    estimado_estadias = sum(float(vehiculo.get("monto") or 0) for vehiculo in vehiculos_activos)
    estimado_lavados = sum(
        float(lavado.get("valor_lavado_snapshot") or 0)
        for lavado in solo_lavados_activos
        if lavado.get("id_ingreso_generado") is None
    )
    estimado_por_cobrar = estimado_estadias + estimado_lavados
    total_turno = float(caja["total_general"])

    return {
        "vehiculos_activos": len(vehiculos_activos),
        "usos_bano": caja["total_banos"],
        "usos_bano_monto": caja["total_banos_monto"],
        "lavados_cobrados": caja["total_lavados_solos"],
        "lavados_cobrados_monto": caja["total_lavados_solos_monto"],
        "mensualidades_mes": mensualidades_mes["cantidad"],
        "mensualidades_mes_monto": mensualidades_mes["monto"],
        "noches_cobradas": caja["total_noches"],
        "noches_cobradas_monto": caja["total_noches_monto"],
        "total_turno": total_turno,
        "gastos": caja["total_gastos"],
        "neto_caja": caja["total_neto"],
        "estimado_por_cobrar": estimado_por_cobrar,
        "total_proyectado": total_turno + estimado_por_cobrar,
    }

@slow_operation("dashboard_refresh")
def obtener_resumen_diario():
    """
    Obtiene el resumen desde el último cierre diario hasta ahora,
    incluyendo:
    - Cantidad total de ingresos desde el último cierre
    - Vehículos actualmente estacionados
    - Total recaudado desde el último cierre
    """
    with db_cursor(dictionary=True) as cursor:
        # Obtener fecha del último cierre
        cursor.execute("SELECT MAX(fecha_cierre) AS ultima_cierre FROM cierres_diarios")
        row = cursor.fetchone()
        fecha_inicio = row["ultima_cierre"] if row and row["ultima_cierre"] else "1970-01-01 00:00:00"

        # Total de ingresos desde último cierre
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM ingresos
            WHERE fecha_hora_ingreso > %s AND fecha_hora_ingreso <= NOW()
              AND NOT EXISTS (
                  SELECT 1 FROM ingresos_eliminados ie
                  WHERE ie.id_ingreso_original = ingresos.id_ingreso
              )
        """, (fecha_inicio,))
        total_ingresos = cursor.fetchone()["total"]

        # Los pagos mensuales son un indicador de mes calendario, incluso si ya cerraron.
        cursor.execute("""
            SELECT COUNT(*) AS cantidad, COALESCE(SUM(monto_snapshot), 0) AS monto
            FROM pagos_mensuales
            WHERE fecha_pago >= DATE_FORMAT(CURDATE(), '%Y-%m-01')
              AND fecha_pago < DATE_ADD(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 1 MONTH)
        """)
        mensualidades_mes = cursor.fetchone() or {"cantidad": 0, "monto": 0}

    # Reuse the daily-close sources so dashboard cards cannot drift from cashbox.
    caja = obtener_resumen_caja_actual()
    vehiculos_activos = obtener_vehiculos_activos()
    solo_lavados_activos = obtener_solo_lavados_activos()
    metricas = calcular_metricas_panel(
        caja,
        vehiculos_activos,
        solo_lavados_activos,
        mensualidades_mes,
    )

    return {
        "total_ingresos": total_ingresos,
        **metricas,
    }


@slow_operation("dashboard_refresh")
def obtener_resumen_banos():
    """
    Obtiene estadísticas de usos de baños desde el último cierre diario hasta ahora.
    """
    caja = obtener_resumen_caja_actual()
    return {
        "cantidad": caja["total_banos"],
        "total": caja["total_banos_monto"],
    }
