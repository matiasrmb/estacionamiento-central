"""
Controlador para la generación de cierres diarios.

Incluye lógica para consolidar ingresos y generar reportes en PDF.
"""

from datetime import datetime

import mysql.connector

from controllers.operaciones_servicio_controller import asegurar_schema_operaciones_servicio
from controllers.mensuales_controller import asegurar_schema_mensuales
from utils.db import db_cursor
from utils.pdf import generar_pdf_cierre


_SCHEMA_CIERRES_ASEGURADO = False
_DUPLICATE_SCHEMA_ERROR_CODES = {1060, 1061}


def _ejecutar_schema(cursor, sentencia):
    try:
        cursor.execute(sentencia)
    except mysql.connector.Error as exc:
        if getattr(exc, "errno", None) not in _DUPLICATE_SCHEMA_ERROR_CODES:
            raise


def asegurar_schema_cierres():
    """Agrega de forma idempotente los campos requeridos por el cierre actual."""
    global _SCHEMA_CIERRES_ASEGURADO
    if _SCHEMA_CIERRES_ASEGURADO:
        return

    # Mantiene operativos los cierres en instalaciones anteriores a Solo lavado.
    asegurar_schema_operaciones_servicio()
    asegurar_schema_mensuales()
    with db_cursor(commit=True) as cursor:
        _ejecutar_schema(cursor, """
            CREATE TABLE IF NOT EXISTS gastos_operacion (
                id_gasto INT AUTO_INCREMENT PRIMARY KEY,
                fecha_hora DATETIME NOT NULL,
                categoria VARCHAR(80) NOT NULL,
                descripcion VARCHAR(500) NOT NULL,
                monto INT NOT NULL,
                usuario VARCHAR(50) NOT NULL,
                id_cierre INT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_gastos_operacion_cierre (id_cierre),
                INDEX idx_gastos_operacion_fecha (fecha_hora),
                FOREIGN KEY (id_cierre) REFERENCES cierres_diarios(id_cierre)
            )
        """)
        for sentencia in (
            "ALTER TABLE cierres_diarios ADD COLUMN total_lavados_solos INT NOT NULL DEFAULT 0",
            "ALTER TABLE cierres_diarios ADD COLUMN total_lavados_solos_monto INT NOT NULL DEFAULT 0",
            "ALTER TABLE cierres_diarios ADD COLUMN total_general INT NOT NULL DEFAULT 0",
            "ALTER TABLE cierres_diarios ADD COLUMN total_gastos INT NOT NULL DEFAULT 0",
            "ALTER TABLE cierres_diarios ADD COLUMN total_neto INT NOT NULL DEFAULT 0",
            "ALTER TABLE usos_bano ADD COLUMN id_cierre INT NULL",
            "ALTER TABLE usos_bano ADD INDEX idx_usos_bano_cierre (id_cierre)",
            "ALTER TABLE operaciones_servicio ADD COLUMN cerrado TINYINT(1) NOT NULL DEFAULT 0",
            "ALTER TABLE operaciones_servicio ADD INDEX idx_operaciones_servicio_cierre (cerrado, estado, fecha_hora_fin)",
        ):
            _ejecutar_schema(cursor, sentencia)

    _SCHEMA_CIERRES_ASEGURADO = True

def realizar_cierre_diario(usuario):
    """
    Realiza el cierre diario de ingresos y genera un resumen en PDF.

    Args:
        usuario (str): Usuario que ejecuta el cierre.

    Returns:
        tuple: (bool, str) indicando si el cierre fue exitoso y un mensaje informativo.
    """
    asegurar_schema_cierres()
    with db_cursor(dictionary=True, commit=True) as cursor:
        cursor.execute("""
            SELECT MAX(fecha_cierre) AS ultimo_cierre
            FROM cierres_diarios
        """)
        ultimo = cursor.fetchone() or {}
        ultimo_cierre = ultimo.get("ultimo_cierre")

        cursor.execute("""
            SELECT id_ingreso, fecha_hora_ingreso, fecha_hora_salida, tarifa_aplicada
            FROM ingresos
            WHERE fecha_hora_salida IS NOT NULL AND cerrado = FALSE
            FOR UPDATE
        """)
        registros = cursor.fetchall()

        fecha_cierre = datetime.now()
        if ultimo_cierre:
            fecha_inicio = ultimo_cierre
        elif registros:
            fecha_inicio = min([r["fecha_hora_ingreso"] for r in registros])
        else:
            fecha_inicio = fecha_cierre.replace(hour=0, minute=0, second=0, microsecond=0)

        total_recaudado = sum(int(r["tarifa_aplicada"] or 0) for r in registros)
        total_ingresos = len(registros)
        total_salidas = total_ingresos  # Ingreso con salida registrada

        # Cada fuente pendiente se bloquea y se vincula al cierre creado abajo.
        cursor.execute("""
            SELECT id, monto
            FROM usos_bano
            WHERE id_cierre IS NULL
            FOR UPDATE
        """)
        banos = cursor.fetchall()
        total_banos = len(banos)
        total_banos_monto = sum(int(bano.get("monto") or 0) for bano in banos)

        cursor.execute("""
            SELECT id_operacion_servicio, valor_lavado_snapshot
            FROM operaciones_servicio
            WHERE estado = 'FINALIZADO_COBRADO' AND cerrado = FALSE
            FOR UPDATE
        """)
        lavados_solos = cursor.fetchall()
        total_lavados_solos = len(lavados_solos)
        total_lavados_solos_monto = sum(
            int(lavado.get("valor_lavado_snapshot") or 0)
            for lavado in lavados_solos
        )

        cursor.execute("""
            SELECT id_gasto, monto
            FROM gastos_operacion
            WHERE id_cierre IS NULL
            FOR UPDATE
        """)
        gastos = cursor.fetchall()
        total_gastos = sum(int(gasto.get("monto") or 0) for gasto in gastos)

        cursor.execute("""
            SELECT id_pago_mensual, monto_snapshot
            FROM pagos_mensuales
            WHERE id_cierre IS NULL
            FOR UPDATE
        """)
        mensualidades = cursor.fetchall()
        total_mensualidades = len(mensualidades)
        total_mensualidades_monto = sum(
            int(pago.get("monto_snapshot") or 0) for pago in mensualidades
        )

        if not registros and not banos and not lavados_solos and not gastos and not mensualidades:
            return False, "No hay registros para cerrar hoy."

        total_general = total_recaudado + total_banos_monto + total_lavados_solos_monto + total_mensualidades_monto
        total_neto = total_general - total_gastos

        # Insertar el resumen en la tabla cierres
        cursor.execute("""
            INSERT INTO cierres_diarios (
                fecha_inicio, fecha_cierre, total_recaudado,
                total_ingresos, total_salidas, total_banos,
                total_banos_monto, total_lavados_solos, total_lavados_solos_monto,
                total_mensualidades, total_mensualidades_monto, total_general, total_gastos,
                total_neto, usuario
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (fecha_inicio, fecha_cierre, total_recaudado,
               total_ingresos, total_salidas, total_banos,
                total_banos_monto, total_lavados_solos,
                total_lavados_solos_monto, total_mensualidades, total_mensualidades_monto,
                total_general, total_gastos,
                total_neto, usuario))
        id_cierre = cursor.lastrowid

        # Marcar ingresos como cerrados
        ids = [r["id_ingreso"] for r in registros]
        if ids:
            formato = ','.join(['%s'] * len(ids))
            cursor.execute(f"""
                UPDATE ingresos SET cerrado = TRUE
                WHERE id_ingreso IN ({formato})
                  AND fecha_hora_salida IS NOT NULL
                  AND cerrado = FALSE
            """, ids)

        ids_banos = [bano["id"] for bano in banos]
        if ids_banos:
            formato = ",".join(["%s"] * len(ids_banos))
            cursor.execute(
                f"UPDATE usos_bano SET id_cierre = %s WHERE id IN ({formato}) AND id_cierre IS NULL",
                [id_cierre, *ids_banos],
            )

        ids_lavados = [lavado["id_operacion_servicio"] for lavado in lavados_solos]
        if ids_lavados:
            formato = ",".join(["%s"] * len(ids_lavados))
            cursor.execute(
                f"UPDATE operaciones_servicio SET cerrado = TRUE WHERE id_operacion_servicio IN ({formato}) AND cerrado = FALSE",
                ids_lavados,
            )

        ids_gastos = [gasto["id_gasto"] for gasto in gastos]
        if ids_gastos:
            formato = ",".join(["%s"] * len(ids_gastos))
            cursor.execute(
                f"UPDATE gastos_operacion SET id_cierre = %s WHERE id_gasto IN ({formato}) AND id_cierre IS NULL",
                [id_cierre, *ids_gastos],
            )

        ids_mensualidades = [pago["id_pago_mensual"] for pago in mensualidades]
        if ids_mensualidades:
            formato = ",".join(["%s"] * len(ids_mensualidades))
            cursor.execute(
                f"UPDATE pagos_mensuales SET id_cierre = %s WHERE id_pago_mensual IN ({formato}) AND id_cierre IS NULL",
                [id_cierre, *ids_mensualidades],
            )

    datos_pdf = {
        "Fecha de inicio": fecha_inicio.strftime("%Y-%m-%d %H:%M"),
        "Fecha de cierre": fecha_cierre.strftime("%Y-%m-%d %H:%M"),
        "Total recaudado vehículos": f"${total_recaudado}",
        "Total baños registrados": total_banos,
        "Total recaudado baños": f"${total_banos_monto}",
        "Lavados solos registrados": total_lavados_solos,
        "Total recaudado lavados solos": f"${total_lavados_solos_monto}",
        "Mensualidades cobradas": total_mensualidades,
        "Total recaudado mensualidades": f"${total_mensualidades_monto}",
        "Total ingresos": total_ingresos,
        "Total salidas": total_salidas,
        "Total general bruto": f"${total_general}",
        "Total gastos": f"${total_gastos}",
        "Total neto del día": f"${total_neto}",
        "Registrado por": usuario
    }
    generar_pdf_cierre("diario", datos_pdf)

    return True, f"Cierre realizado con éxito. Total neto: ${total_neto}"

