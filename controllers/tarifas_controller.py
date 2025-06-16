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
        from utils.db import get_connection
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT valor
            FROM tarifas_personalizadas
            WHERE %s BETWEEN minuto_inicio AND minuto_fin
            ORDER BY minuto_inicio ASC
            LIMIT 1
        """, (minutos,))
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()

        if resultado:
            return resultado["valor"]
        else:
            return int(config.get("tarifa_minima", 300))

    else:
        # Fallback a tarifa mínima
        return int(config.get("tarifa_minima", 300))
