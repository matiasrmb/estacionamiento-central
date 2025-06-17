from utils.db import get_connection
from controllers.config_controller import obtener_configuracion

def obtener_tarifas_personalizadas():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id_tarifa, minuto_inicio, minuto_fin, valor
        FROM tarifas_personalizadas
        ORDER BY minuto_inicio ASC
    """)
    resultado = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultado

def agregar_intervalo(min_inicio, min_fin, valor):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tarifas_personalizadas (minuto_inicio, minuto_fin, valor)
        VALUES (%s, %s, %s)
    """, (min_inicio, min_fin, valor))
    conn.commit()
    cursor.close()
    conn.close()

def eliminar_intervalo(id_tarifa):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tarifas_personalizadas WHERE id_tarifa = %s", (id_tarifa,))
    conn.commit()
    cursor.close()
    conn.close()

def actualizar_intervalo(id_tarifa, min_inicio, min_fin, valor):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tarifas_personalizadas
        SET minuto_inicio = %s, minuto_fin = %s, valor = %s
        WHERE id_tarifa = %s
    """, (min_inicio, min_fin, valor, id_tarifa))
    conn.commit()
    cursor.close()
    conn.close()

def calcular_tarifa(minutos):
    config = obtener_configuracion()
    modo = config.get("modo_cobro", "minuto")

    if modo == "minuto":
        tarifa_por_minuto = int(config.get("tarifa_hora", 1300)) / 60
        return round(minutos * tarifa_por_minuto)

    elif modo == "personalizado":
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Obtener todos los intervalos
        cursor.execute("""
            SELECT minuto_inicio, minuto_fin, valor
            FROM tarifas_personalizadas
            ORDER BY minuto_inicio ASC
        """)
        intervalos = cursor.fetchall()
        cursor.close()
        conn.close()

        if not intervalos:
            return int(config.get("tarifa_minima", 300))

        minutos_en_hora = minutos % 60
        horas_completas = minutos // 60

        # Buscar el tramo correspondiente dentro del ciclo de 60 minutos
        for tramo in intervalos:
            if tramo["minuto_inicio"] <= minutos_en_hora <= tramo["minuto_fin"]:
                return tramo["valor"] + horas_completas * intervalos[-1]["valor"]

        # Si por algún motivo no encaja, usar el último tramo como base
        return intervalos[-1]["valor"] + horas_completas * intervalos[-1]["valor"]

    else:
        # Fallback a tarifa mínima si modo no reconocido
        return int(config.get("tarifa_minima", 300))

