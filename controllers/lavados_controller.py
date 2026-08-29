"""
Controlador de lavados de vehículos.

Los lavados pausan el cobro de estacionamiento mientras están activos y
mantienen el valor aplicado en el momento de inicio para auditoría histórica.
"""

from datetime import datetime

from controllers.config_controller import LAVADO_CATEGORIAS, obtener_valores_lavado
from utils.db import db_cursor


def obtener_categorias_lavado(configuracion=None):
    """
    Retorna categorías de lavado disponibles con sus valores configurados.
    """
    return obtener_valores_lavado(configuracion)


def _categoria_valida(categoria_lavado):
    return categoria_lavado in {clave for clave, _, _ in LAVADO_CATEGORIAS}


def iniciar_lavado(id_ingreso, categoria_lavado, usuario):
    """
    Inicia un lavado para un ingreso activo.

    Args:
        id_ingreso (int): Ingreso activo del vehículo.
        categoria_lavado (str): Clave de categoría configurada.
        usuario (str): Usuario operador.

    Returns:
        dict | None: Datos del lavado iniciado o None si no se pudo iniciar.
    """
    if not _categoria_valida(categoria_lavado):
        raise ValueError("Categoría de lavado inválida.")

    valores = obtener_categorias_lavado()
    valor_lavado = valores[categoria_lavado]["valor"]
    ahora = datetime.now()

    with db_cursor(dictionary=True, commit=True) as cursor:
        cursor.execute("""
            SELECT i.id_ingreso, i.id_vehiculo, i.en_lavado, v.patente
            FROM ingresos i
            JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
            WHERE i.id_ingreso = %s
              AND i.fecha_hora_salida IS NULL
              AND NOT EXISTS (
                  SELECT 1 FROM ingresos_eliminados ie
                  WHERE ie.id_ingreso_original = i.id_ingreso
              )
            LIMIT 1
        """, (id_ingreso,))
        ingreso = cursor.fetchone()

        if not ingreso or ingreso.get("en_lavado"):
            return None

        cursor.execute("""
            INSERT INTO lavados (
                id_ingreso, id_vehiculo, patente, categoria_lavado,
                valor_lavado, fecha_hora_inicio, usuario_inicio, estado
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'activo')
        """, (
            ingreso["id_ingreso"],
            ingreso["id_vehiculo"],
            ingreso["patente"],
            categoria_lavado,
            valor_lavado,
            ahora,
            usuario,
        ))
        id_lavado = cursor.lastrowid

        cursor.execute(
            "UPDATE ingresos SET en_lavado = 1 WHERE id_ingreso = %s",
            (id_ingreso,)
        )

    return {
        "id_lavado": id_lavado,
        "id_ingreso": id_ingreso,
        "categoria_lavado": categoria_lavado,
        "valor_lavado": valor_lavado,
        "fecha_hora_inicio": ahora,
    }


def finalizar_lavado(id_ingreso, usuario):
    """
    Finaliza el lavado activo de un ingreso y reactiva el cobro normal.
    """
    ahora = datetime.now()

    with db_cursor(dictionary=True, commit=True) as cursor:
        cursor.execute("""
            SELECT id_lavado, categoria_lavado, valor_lavado, fecha_hora_inicio
            FROM lavados
            WHERE id_ingreso = %s
              AND estado = 'activo'
              AND fecha_hora_fin IS NULL
            ORDER BY fecha_hora_inicio DESC
            LIMIT 1
        """, (id_ingreso,))
        lavado = cursor.fetchone()

        if not lavado:
            return None

        cursor.execute("""
            UPDATE lavados
            SET fecha_hora_fin = %s,
                usuario_fin = %s,
                estado = 'finalizado'
            WHERE id_lavado = %s
        """, (ahora, usuario, lavado["id_lavado"]))

        cursor.execute(
            "UPDATE ingresos SET en_lavado = 0 WHERE id_ingreso = %s",
            (id_ingreso,)
        )

    return {
        "id_lavado": lavado["id_lavado"],
        "id_ingreso": id_ingreso,
        "categoria_lavado": lavado["categoria_lavado"],
        "valor_lavado": lavado["valor_lavado"],
        "fecha_hora_inicio": lavado["fecha_hora_inicio"],
        "fecha_hora_fin": ahora,
    }


def obtener_lavados_por_ingreso(id_ingreso):
    """
    Obtiene todos los lavados asociados a un ingreso.
    """
    with db_cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT id_lavado, id_ingreso, categoria_lavado, valor_lavado,
                   fecha_hora_inicio, fecha_hora_fin, estado
            FROM lavados
            WHERE id_ingreso = %s
            ORDER BY fecha_hora_inicio ASC
        """, (id_ingreso,))
        return cursor.fetchall()


def calcular_minutos_lavado(id_ingreso, fecha_hora_salida=None):
    """
    Calcula minutos a descontar por lavados finalizados o activos.
    """
    fin_calculo = fecha_hora_salida or datetime.now()
    total = 0

    for lavado in obtener_lavados_por_ingreso(id_ingreso):
        inicio = lavado["fecha_hora_inicio"]
        fin = lavado["fecha_hora_fin"] or fin_calculo

        if fin > inicio:
            total += int((fin - inicio).total_seconds() / 60)

    return total


def obtener_intervalos_lavado(id_ingreso, fecha_hora_salida=None):
    """Retorna los intervalos de lavado acotados al momento de cálculo."""
    fin_calculo = fecha_hora_salida or datetime.now()
    intervalos = []

    for lavado in obtener_lavados_por_ingreso(id_ingreso):
        inicio = lavado["fecha_hora_inicio"]
        fin = min(lavado["fecha_hora_fin"] or fin_calculo, fin_calculo)
        if fin > inicio:
            intervalos.append((inicio, fin))

    return intervalos


def calcular_total_lavados(id_ingreso):
    """
    Calcula el total monetario de lavados asociados a un ingreso.

    El lavado pausa el cobro de estacionamiento, pero su valor propio se cobra
    junto con la salida del vehículo.
    """
    total = 0
    for lavado in obtener_lavados_por_ingreso(id_ingreso):
        total += int(lavado.get("valor_lavado") or 0)
    return total


def obtener_minutos_lavado_por_ingresos(id_ingresos, fecha_hora_salida=None):
    """
    Calcula minutos de lavado por ingreso en una sola consulta.
    """
    if not id_ingresos:
        return {}

    fin_calculo = fecha_hora_salida or datetime.now()
    placeholders = ", ".join(["%s"] * len(id_ingresos))

    with db_cursor(dictionary=True) as cursor:
        cursor.execute(f"""
            SELECT id_ingreso, fecha_hora_inicio, fecha_hora_fin
            FROM lavados
            WHERE id_ingreso IN ({placeholders})
        """, tuple(id_ingresos))
        lavados = cursor.fetchall()

    minutos_por_ingreso = {id_ingreso: 0 for id_ingreso in id_ingresos}
    for lavado in lavados:
        inicio = lavado["fecha_hora_inicio"]
        fin = lavado["fecha_hora_fin"] or fin_calculo
        if fin > inicio:
            minutos_por_ingreso[lavado["id_ingreso"]] += int((fin - inicio).total_seconds() / 60)

    return minutos_por_ingreso


def obtener_totales_lavado_por_ingresos(id_ingresos):
    """
    Calcula el total monetario de lavados por ingreso en una sola consulta.
    """
    if not id_ingresos:
        return {}

    placeholders = ", ".join(["%s"] * len(id_ingresos))

    with db_cursor(dictionary=True) as cursor:
        cursor.execute(f"""
            SELECT id_ingreso, COALESCE(SUM(valor_lavado), 0) AS total_lavados
            FROM lavados
            WHERE id_ingreso IN ({placeholders})
            GROUP BY id_ingreso
        """, tuple(id_ingresos))
        rows = cursor.fetchall()

    return {row["id_ingreso"]: int(row["total_lavados"] or 0) for row in rows}
