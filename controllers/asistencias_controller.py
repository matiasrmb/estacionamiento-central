from utils.db import get_connection

def obtener_asistencias(usuario=None, fecha_inicio=None, fecha_fin=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT usuario, hora_inicio, hora_salida, cantidad_movimientos, total_recaudado
        FROM asistencias
        WHERE 1=1
    """
    params = []

    if usuario:
        query += " AND usuario = %s"
        params.append(usuario)

    if fecha_inicio and fecha_fin:
        query += " AND hora_inicio BETWEEN %s AND %s"
        params.extend([fecha_inicio, fecha_fin])

    query += " ORDER BY hora_inicio DESC"

    cursor.execute(query, params)
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados