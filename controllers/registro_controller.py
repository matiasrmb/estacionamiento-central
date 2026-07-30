"""
Controlador de operaciones de ingreso, salida y estado de vehículos en el estacionamiento.
"""

from datetime import datetime, timedelta
import json

from utils.db import db_cursor
from utils.print_jobs import (
    crear_print_job_ingreso,
    crear_print_job_salida,
    salida_idempotency_key,
)
from controllers.tarifas_controller import (
    calcular_tarifa,
    calcular_tarifa_con_contexto,
    describir_detalle_tarifa,
    obtener_contexto_tarifa,
)
from controllers.config_controller import (
    obtener_configuracion,
    obtener_print_jobs_pc_activos,
)
from controllers.lavados_controller import (
    asegurar_schema_lavados,
    calcular_minutos_lavado,
    calcular_total_lavados,
    obtener_minutos_lavado_por_ingresos,
    obtener_totales_lavado_por_ingresos,
)
from controllers.operaciones_servicio_controller import obtener_operacion_convertida_por_ingreso
from utils.slowlog import slow_operation


def calcular_minutos_estadia(fecha_hora_ingreso, fecha_hora_salida=None):
    """
    Calcula los minutos de estadía entre ingreso y salida.

    Si la salida es anterior al ingreso, retorna 0 para evitar tarifas
    negativas por desfases de reloj o datos inconsistentes.
    """
    salida = fecha_hora_salida or datetime.now()
    minutos = int((salida - fecha_hora_ingreso).total_seconds() / 60)
    return max(minutos, 0)


def obtener_ingreso_activo_priorizado(patente, contexto="operación"):
    """
    Obtiene el ingreso activo prioritario de una patente.

    Reutiliza el orden definido por obtener_ingresos_activos_por_patente:
    primero ingresos normales y luego los más recientes. Si existen varios
    activos, deja una advertencia para facilitar la detección de inconsistencias.
    """
    activos = obtener_ingresos_activos_por_patente(patente)

    if not activos:
        return None

    if len(activos) > 1:
        print(
            f"[WARN] La patente {patente} tiene {len(activos)} ingresos activos. "
            f"Se usará el primero priorizado para {contexto}."
        )

    return activos[0]


def obtener_ingresos_activos_por_patente(patente):
    """
    Obtiene todos los ingresos activos de una patente, priorizados de forma útil
    para la lógica del sistema.

    Prioridad:
    1. ingresos no marcados en espera
    2. ingresos más recientes

    Args:
        patente (str): Patente del vehículo.

    Returns:
        list[dict]: Lista de ingresos activos de la patente.
    """
    asegurar_schema_lavados()
    with db_cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT
                i.id_ingreso,
                i.id_vehiculo,
                i.fecha_hora_ingreso,
                i.fecha_hora_salida,
                i.en_espera,
                i.en_lavado,
                i.tarifa_aplicada,
                i.reingresado,
                v.patente
            FROM ingresos i
            JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
            WHERE v.patente = %s
              AND i.fecha_hora_salida IS NULL
            ORDER BY i.en_espera ASC, i.fecha_hora_ingreso DESC
        """, (patente,))
        return cursor.fetchall()


def buscar_estado_vehiculo(patente):
    """
    Determina el estado actual del vehículo.

    Args:
        patente (str): Patente del vehículo.

    Returns:
        str: "no_registrado", "dentro" o "fuera".
    """
    try:
        with db_cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT id_vehiculo FROM vehiculos WHERE patente = %s LIMIT 1",
                (patente,)
            )
            vehiculo = cursor.fetchone()

        if not vehiculo:
            return "no_registrado"

        activos = obtener_ingresos_activos_por_patente(patente)

        if activos:
            if len(activos) > 1:
                print(f"[WARN] La patente {patente} tiene {len(activos)} ingresos activos.")
            return "dentro"

        return "fuera"

    except Exception as e:
        print(f"Error en buscar_estado_vehiculo: {e}")
        return None


def validar_fecha_hora_ingreso_personalizada(fecha_hora_ingreso, ahora=None):
    """
    Valida una hora de ingreso personalizada para casos de carga tardía.

    La fecha debe corresponder al día actual, no puede estar en el futuro y
    solo se admite un atraso máximo de 4 horas.
    """
    if fecha_hora_ingreso is None:
        return False, "Ingresa una hora de ingreso."

    ahora = ahora or datetime.now()

    if fecha_hora_ingreso.date() != ahora.date():
        return False, "La hora personalizada debe ser del día actual."

    if fecha_hora_ingreso > ahora:
        return False, "La hora personalizada no puede ser futura."

    if fecha_hora_ingreso < ahora - timedelta(hours=4):
        return False, "La hora personalizada no puede tener más de 4 horas de antigüedad."

    return True, ""


def registrar_ingreso(patente, fecha_hora_ingreso=None):
    """
    Registra la entrada de un vehículo al estacionamiento.

    No permite crear un nuevo ingreso si la patente ya tiene un ingreso activo.

    Args:
        patente (str): Patente del vehículo.

    Returns:
        bool: True si se registró correctamente, False en caso contrario.
    """
    resultado = registrar_ingreso_detallado(patente, fecha_hora_ingreso)
    return bool(resultado)


@slow_operation("registration")
def registrar_ingreso_detallado(patente, fecha_hora_ingreso=None):
    """
    Registra la entrada de un vehículo y retorna datos para feedback de UI.

    Returns:
        dict | None: Datos del ingreso registrado o None si falló.
    """
    try:
        es_ingreso_personalizado = fecha_hora_ingreso is not None
        if es_ingreso_personalizado:
            es_valida, mensaje = validar_fecha_hora_ingreso_personalizada(fecha_hora_ingreso)
            if not es_valida:
                print(f"[WARN] No se registró ingreso para {patente}: {mensaje}")
                return None

        with db_cursor(commit=True) as cursor:
            cursor.execute(
                "SELECT id_vehiculo FROM vehiculos WHERE patente = %s FOR UPDATE",
                (patente,)
            )
            row = cursor.fetchone()

            if row:
                id_vehiculo = row[0]
            else:
                cursor.execute(
                    "INSERT INTO vehiculos (patente, tipo_cliente) VALUES (%s, 'ocasional')",
                    (patente,)
                )
                id_vehiculo = cursor.lastrowid

            # This vehicle lock also serializes a registration with a salida reversal.
            cursor.execute("""
                SELECT id_ingreso
                FROM ingresos
                WHERE id_vehiculo = %s
                  AND fecha_hora_salida IS NULL
                FOR UPDATE
            """, (id_vehiculo,))
            if cursor.fetchone():
                print(f"[WARN] No se registró ingreso para {patente}: ya existe un ingreso activo.")
                return None

            fecha_hora = fecha_hora_ingreso if es_ingreso_personalizado else datetime.now()

            cursor.execute("""
                INSERT INTO ingresos (id_vehiculo, fecha_hora_ingreso, en_espera)
                VALUES (%s, %s, 0)
            """, (id_vehiculo, fecha_hora))
            id_ingreso = cursor.lastrowid
            if obtener_print_jobs_pc_activos(cursor):
                crear_print_job_ingreso(cursor, id_ingreso, patente, fecha_hora)

    except Exception as e:
        print(f"Error al registrar ingreso: {e}")
        return None

    return {
        "patente": patente,
        "fecha_hora_ingreso": fecha_hora,
    }


def registrar_salida(patente, usuario):
    """
    Registra la salida de un vehículo y calcula la tarifa correspondiente.

    Si existieran múltiples ingresos activos por inconsistencia previa,
    se prioriza el ingreso activo normal (no en espera). Si no existe,
    se usa el ingreso en espera más reciente.

    Args:
        patente (str): Patente del vehículo.
        usuario (str): Usuario que registra la salida.

    Returns:
        int | None: Tarifa calculada o None si hubo error.
    """
    resultado = registrar_salida_detallada(patente, usuario)
    return resultado["tarifa"] if resultado else None


@slow_operation("exit")
def registrar_salida_detallada(patente, usuario):
    """
    Registra la salida de un vehículo y retorna datos para feedback de UI.

    Returns:
        dict | None: Datos de la salida registrada o None si falló.
    """
    try:
        ingreso = obtener_ingreso_activo_priorizado(patente, "registrar salida")

        if not ingreso:
            return None

        if ingreso.get("en_lavado"):
            print(f"[WARN] No se registró salida para {patente}: el vehículo está en lavado.")
            return None

        fecha_ingreso = ingreso["fecha_hora_ingreso"]
        ahora = datetime.now()
        minutos_totales = calcular_minutos_estadia(fecha_ingreso, ahora)
        minutos_lavado = calcular_minutos_lavado(ingreso["id_ingreso"], ahora)
        minutos = max(minutos_totales - minutos_lavado, 0)

        tarifa, subida_aplicada, monto_extra = calcular_tarifa(
            minutos,
            fecha_ingreso,
            ahora,
            devolver_flag=True
        )
        total_lavados = calcular_total_lavados(ingreso["id_ingreso"])
        operacion_convertida = obtener_operacion_convertida_por_ingreso(ingreso["id_ingreso"])
        detalle_secciones = None
        if operacion_convertida:
            total_lavados += int(operacion_convertida.get("valor_lavado_snapshot") or 0)
            detalle_secciones = _build_detalle_salida_lavado_convertido(
                operacion_convertida,
                fecha_ingreso,
                ahora,
                tarifa,
                minutos,
            )
        total_a_cobrar = tarifa + total_lavados

        try:
            config = obtener_configuracion()
        except Exception:
            # The ticket metadata may use the configured payment mode, but a
            # configuration read must never prevent recording a completed exit.
            config = {}
        modo_cobro = config.get("modo_cobro", "minuto")
        detalle_cobro = (
            describir_detalle_tarifa(minutos)
            if modo_cobro == "personalizado"
            else None
        )

        with db_cursor(commit=True) as cursor:
            cursor.execute("""
                UPDATE ingresos
                SET fecha_hora_salida = %s,
                    tarifa_aplicada = %s,
                    usuario = %s
                WHERE id_ingreso = %s
                  AND fecha_hora_salida IS NULL
            """, (ahora, total_a_cobrar, usuario, ingreso["id_ingreso"]))

            if cursor.rowcount != 1:
                print(f"[WARN] No se registró salida para {patente}: el ingreso ya fue cerrado.")
                return None

            if obtener_print_jobs_pc_activos(cursor):
                cursor.execute("""
                    SELECT idempotency_key
                    FROM print_jobs
                    WHERE id_ingreso = %s
                      AND tipo = 'TICKET_SALIDA'
                    FOR UPDATE
                """, (ingreso["id_ingreso"],))
                claves_existentes = {job[0] for job in cursor.fetchall()}
                secuencia_reingreso = 0
                clave_idempotencia = salida_idempotency_key(ingreso["id_ingreso"])
                while clave_idempotencia in claves_existentes:
                    secuencia_reingreso += 1
                    clave_idempotencia = salida_idempotency_key(
                        ingreso["id_ingreso"], secuencia_reingreso
                    )
                crear_print_job_salida(
                    cursor,
                    ingreso["id_ingreso"],
                    patente,
                    fecha_ingreso,
                    ahora,
                    minutos,
                    total_a_cobrar,
                    detalle_cobro,
                    tarifa,
                    total_lavados,
                    usuario,
                    modo_cobro,
                    subida_aplicada,
                    monto_extra,
                    detalle_secciones,
                    clave_idempotencia,
                )

    except Exception as e:
        print(f"Error al registrar salida: {e}")
        return None

    return {
        "patente": patente,
        "fecha_hora_ingreso": fecha_ingreso,
        "fecha_hora_salida": ahora,
        "minutos": minutos,
        "tarifa": total_a_cobrar,
        "tarifa_estacionamiento": tarifa,
        "total_lavados": total_lavados,
    }


def _build_detalle_salida_lavado_convertido(operacion, fecha_ingreso, fecha_hora_salida, tarifa_estadia, minutos_estadia):
    inicio_lavado = operacion.get("fecha_hora_inicio")
    fin_lavado = operacion.get("fecha_hora_fin") or fecha_ingreso
    minutos_lavado = calcular_minutos_estadia(inicio_lavado, fin_lavado) if inicio_lavado else 0
    monto_lavado = int(operacion.get("valor_lavado_snapshot") or 0)

    return {
        "lavado": {
            "inicio": inicio_lavado,
            "fin": fin_lavado,
            "duracion_minutos": minutos_lavado,
            "monto": monto_lavado,
        },
        "estadia": {
            "inicio": fecha_ingreso,
            "fin": fecha_hora_salida,
            "duracion_minutos": minutos_estadia,
            "monto": tarifa_estadia,
        },
    }


@slow_operation("table_refresh")
def obtener_vehiculos_activos():
    """
    Obtiene la lista de vehículos actualmente estacionados.

    Returns:
        list[dict]: Lista con patente, hora de ingreso y monto acumulado.
    """
    asegurar_schema_lavados()
    with db_cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT
                i.id_ingreso,
                v.patente,
                i.fecha_hora_ingreso,
                i.en_espera,
                i.en_lavado
            FROM ingresos i
            JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
            WHERE i.fecha_hora_salida IS NULL
            ORDER BY i.fecha_hora_ingreso ASC
        """)
        resultados = cursor.fetchall()

    ahora = datetime.now()
    contexto_tarifa = obtener_contexto_tarifa()
    minutos_lavado_por_ingreso = obtener_minutos_lavado_por_ingresos(
        [r["id_ingreso"] for r in resultados],
        ahora,
    )
    totales_lavado_por_ingreso = obtener_totales_lavado_por_ingresos(
        [r["id_ingreso"] for r in resultados]
    )
    lista = []

    for r in resultados:
        fecha_ingreso = r["fecha_hora_ingreso"]
        minutos_totales = calcular_minutos_estadia(fecha_ingreso, ahora)
        minutos_lavado = minutos_lavado_por_ingreso.get(r["id_ingreso"], 0)
        minutos = max(minutos_totales - minutos_lavado, 0)

        tarifa = (
            calcular_tarifa_con_contexto(minutos, fecha_ingreso, ahora, contexto_tarifa)
            if r["en_espera"] == 0
            else 0
        )
        total_lavados = totales_lavado_por_ingreso.get(r["id_ingreso"], 0)
        monto = tarifa + total_lavados

        lista.append({
            "id_ingreso": r["id_ingreso"],
            "patente_base": r["patente"],
            "patente": r["patente"]
                + (" [EN ESPERA]" if r["en_espera"] else "")
                + (" [EN LAVADO]" if r["en_lavado"] else ""),
            "hora": fecha_ingreso.strftime("%Y-%m-%d %H:%M:%S"),
            "monto": monto,
            "en_espera": bool(r["en_espera"]),
            "en_lavado": bool(r["en_lavado"]),
            "minutos": minutos,
            "total_lavados": total_lavados,
        })

    return lista


def obtener_patentes_cerradas_turno_actual():
    """
    Obtiene las estadías cerradas del turno/día actual aún no cerradas.

    Returns:
        list[dict]: Ingresos con salida y cerrado=FALSE.
    """
    with db_cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT i.id_ingreso,
                   v.patente,
                   i.fecha_hora_ingreso,
                   i.fecha_hora_salida,
                   i.tarifa_aplicada,
                   i.usuario
            FROM ingresos i
            JOIN vehiculos v ON v.id_vehiculo = i.id_vehiculo
            WHERE i.fecha_hora_salida IS NOT NULL
              AND i.cerrado = FALSE
              AND DATE(i.fecha_hora_salida) = CURDATE()
            ORDER BY i.fecha_hora_salida DESC, i.id_ingreso DESC
        """)
        return cursor.fetchall()


def normalizar_patente_busqueda(valor):
    """Normaliza una patente para comparar búsquedas sin separadores."""
    return "".join(caracter for caracter in str(valor or "").upper() if caracter.isalnum())


def _distancia_edicion(origen, destino):
    anterior = list(range(len(destino) + 1))
    for indice_origen, caracter_origen in enumerate(origen, start=1):
        actual = [indice_origen]
        for indice_destino, caracter_destino in enumerate(destino, start=1):
            actual.append(min(
                anterior[indice_destino] + 1,
                actual[indice_destino - 1] + 1,
                anterior[indice_destino - 1] + (caracter_origen != caracter_destino),
            ))
        anterior = actual
    return anterior[-1]


def _fecha_orden_f4(fila):
    fecha = fila.get("fecha_hora_salida") if fila.get("fecha_hora_salida") else fila.get("fecha_hora_ingreso")
    if isinstance(fecha, datetime):
        return fecha
    if isinstance(fecha, str):
        for formato in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(fecha, formato)
            except ValueError:
                continue
    return datetime.max


def _puntaje_similitud_f4(consulta, patente):
    distancia = _distancia_edicion(consulta, patente)
    longitud = max(len(consulta), len(patente))
    if patente == consulta:
        coincidencia_directa = 0
    elif patente.startswith(consulta):
        coincidencia_directa = 1
    elif consulta in patente:
        coincidencia_directa = 2
    else:
        coincidencia_directa = 3

    # La distancia manda; prefijo y contiene solo resuelven similitudes empatadas.
    return (
        patente != consulta,
        distancia,
        distancia / longitud,
        coincidencia_directa,
    )


def ordenar_patentes_turno_para_f4(filas, consulta):
    """Filtra y ordena candidatos F4 por coincidencia y antigüedad del movimiento."""
    consulta_normalizada = normalizar_patente_busqueda(consulta)
    if not consulta_normalizada:
        return sorted(
            filas,
            key=lambda fila: (str(fila.get("patente") or "").upper(), fila.get("id_ingreso", 0)),
        )

    distancia_maxima = max(1, len(consulta_normalizada) // 4)
    candidatos = []
    for fila in filas:
        patente = normalizar_patente_busqueda(fila.get("patente"))
        distancia = _distancia_edicion(consulta_normalizada, patente)
        if consulta_normalizada in patente or distancia <= distancia_maxima:
            candidatos.append((fila, _puntaje_similitud_f4(consulta_normalizada, patente)))

    return [
        fila for fila, _ in sorted(
            candidatos,
            key=lambda candidato: (
                candidato[1],
                _fecha_orden_f4(candidato[0]),
                candidato[0].get("id_ingreso", 0),
            ),
        )
    ]


def obtener_patentes_turno_actual_para_f4():
    """
    Obtiene patentes abiertas y cerradas del turno actual para navegación rápida.

    Incluye ingresos activos y salidas del día/turno actual que aún no fueron
    cerradas en caja. Devuelve una fila por patente/ingreso ordenada por patente.
    """
    activos = obtener_vehiculos_activos()
    cerrados = obtener_patentes_cerradas_turno_actual()

    filas = []
    for activo in activos:
        filas.append({
            "id_ingreso": activo["id_ingreso"],
            "patente": activo.get("patente_base") or str(activo["patente"]).split()[0],
            "estado": "ABIERTO",
            "fecha_hora_ingreso": activo["hora"],
            "fecha_hora_salida": None,
            "minutos": int(activo.get("minutos") or 0),
            "monto": float(activo.get("monto") or 0),
            "en_espera": bool(activo.get("en_espera")),
            "en_lavado": bool(activo.get("en_lavado")),
        })

    for cerrado in cerrados:
        ingreso = cerrado["fecha_hora_ingreso"]
        salida = cerrado["fecha_hora_salida"]
        minutos = int((salida - ingreso).total_seconds() // 60) if ingreso and salida else 0
        filas.append({
            "id_ingreso": cerrado["id_ingreso"],
            "patente": cerrado["patente"],
            "estado": "CERRADO",
            "fecha_hora_ingreso": ingreso,
            "fecha_hora_salida": salida,
            "minutos": minutos,
            "monto": float(cerrado.get("tarifa_aplicada") or 0),
            "usuario": cerrado.get("usuario"),
        })

    return sorted(filas, key=lambda row: (str(row["patente"]).upper(), row["estado"]))


def obtener_ultimo_ingreso_cerrado_por_patente(patente):
    """
    Obtiene la última estadía cerrada de una patente para monitoreo.

    Returns:
        dict | None: Último ingreso con salida, o None si no hay historial cerrado.
    """
    with db_cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT i.id_ingreso,
                   v.patente,
                   i.fecha_hora_ingreso,
                   i.fecha_hora_salida,
                   i.tarifa_aplicada,
                   i.usuario
            FROM ingresos i
            JOIN vehiculos v ON v.id_vehiculo = i.id_vehiculo
            WHERE UPPER(v.patente) = UPPER(%s)
              AND i.fecha_hora_salida IS NOT NULL
            ORDER BY i.fecha_hora_salida DESC, i.id_ingreso DESC
            LIMIT 1
        """, (patente,))
        return cursor.fetchone()


def obtener_total_vehiculos_pagados_turno_actual():
    """
    Obtiene el total cobrado a vehículos que ya salieron y aún no fueron cerrados.

    Returns:
        float: Suma de tarifas aplicadas en el turno actual.
    """
    with db_cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT COALESCE(SUM(tarifa_aplicada), 0) AS total
            FROM ingresos
            WHERE fecha_hora_salida IS NOT NULL
              AND cerrado = FALSE
        """)
        resultado = cursor.fetchone()

    if not resultado:
        return 0.0

    return float(resultado["total"] or 0)


def obtener_ingresos_editables():
    """
    Obtiene ingresos marcados como 'en espera' o 'cerrados', aún visibles para edición manual.

    Returns:
        list[dict]: Lista con id_ingreso, patente, fecha_hora_ingreso y estado.
    """
    with db_cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT i.id_ingreso, v.patente, i.fecha_hora_ingreso, 'EN ESPERA' AS estado
            FROM ingresos i
            JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
            WHERE i.en_espera = 1 AND i.fecha_hora_salida IS NULL
        """)
        en_espera = cursor.fetchall()

        cursor.execute("""
            SELECT i.id_ingreso, v.patente, i.fecha_hora_ingreso, 'CERRADO' AS estado
            FROM ingresos i
            JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
            WHERE i.fecha_hora_salida IS NOT NULL
              AND i.reingresado = 0
              AND i.id_ingreso IN (
                  SELECT MAX(i2.id_ingreso)
                  FROM ingresos i2
                  JOIN vehiculos v2 ON i2.id_vehiculo = v2.id_vehiculo
                  WHERE i2.fecha_hora_salida IS NOT NULL
                    AND i2.reingresado = 0
                  GROUP BY v2.patente
              )
        """)
        cerrados = cursor.fetchall()

    return en_espera + cerrados


def eliminar_ingreso_con_respaldo(id_ingreso, usuario):
    """
    Elimina con respaldo únicamente un ingreso abierto marcado en espera.

    Los trabajos de impresión vinculados se conservan. Los reintentables se
    cancelan y todos se desvinculan del ingreso antes de eliminarlo para
    respetar su clave foránea.

    Args:
        id_ingreso (int): ID del ingreso a eliminar.
        usuario (str): Usuario que realiza la eliminación.

    Returns:
        tuple[bool, str]: Resultado y mensaje para mostrar al operador.
    """
    try:
        with db_cursor(dictionary=True, commit=True) as cursor:
            cursor.execute("""
                SELECT i.id_ingreso, v.patente, i.fecha_hora_ingreso,
                       i.fecha_hora_salida, i.en_espera
                FROM ingresos i
                JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
                WHERE i.id_ingreso = %s
                FOR UPDATE
            """, (id_ingreso,))
            ingreso = cursor.fetchone()

            if not ingreso:
                return False, "El ingreso ya no existe."

            if ingreso["fecha_hora_salida"] is not None:
                return False, "No se puede eliminar un ingreso cerrado."

            if not ingreso["en_espera"]:
                return False, "Solo se pueden eliminar ingresos abiertos en espera."

            cursor.execute("""
                SELECT id_print_job, estado
                FROM print_jobs
                WHERE id_ingreso = %s
                FOR UPDATE
            """, (id_ingreso,))
            jobs = cursor.fetchall()
            if any(job["estado"] == "IMPRIMIENDO" for job in jobs):
                return False, (
                    "No se puede eliminar el ingreso mientras se está imprimiendo "
                    "un ticket asociado."
                )

            cursor.execute("""
                UPDATE print_jobs
                SET estado = 'CANCELADO'
                WHERE id_ingreso = %s
                  AND estado IN ('PENDIENTE', 'ERROR', 'REVISION_MANUAL')
            """, (id_ingreso,))

            cursor.execute("""
                UPDATE print_jobs
                SET id_ingreso = NULL
                WHERE id_ingreso = %s
            """, (id_ingreso,))

            cursor.execute("""
                INSERT INTO ingresos_eliminados (
                    id_ingreso_original,
                    patente,
                    fecha_hora_ingreso,
                    usuario_eliminador
                )
                VALUES (%s, %s, %s, %s)
            """, (
                id_ingreso,
                ingreso["patente"],
                ingreso["fecha_hora_ingreso"],
                usuario
            ))

            cursor.execute("DELETE FROM ingresos WHERE id_ingreso = %s", (id_ingreso,))
        return True, "Ingreso en espera eliminado correctamente."

    except Exception as e:
        print(f"Error al eliminar ingreso en espera: {e}")
        return False, (
            "No se pudo eliminar el ingreso en espera porque tiene dependencias "
            "que impiden conservar su historial."
        )


def marcar_ingreso_en_espera(patente):
    """
    Marca como 'en espera' el ingreso activo normal más reciente de una patente.

    Args:
        patente (str): Patente del vehículo.

    Returns:
        bool: True si se marcó correctamente, False en caso contrario.
    """
    try:
        with db_cursor(dictionary=True, commit=True) as cursor:
            cursor.execute("""
                SELECT i.id_ingreso
                FROM ingresos i
                JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
                WHERE v.patente = %s
                  AND i.fecha_hora_salida IS NULL
                  AND i.en_espera = 0
                ORDER BY i.fecha_hora_ingreso DESC
                LIMIT 1
            """, (patente,))
            ingreso = cursor.fetchone()

            if not ingreso:
                return False

            cursor.execute("""
                UPDATE ingresos
                SET en_espera = 1
                WHERE id_ingreso = %s
            """, (ingreso["id_ingreso"],))

            return cursor.rowcount > 0

    except Exception as e:
        print(f"Error al marcar en espera: {e}")
        return False


def registrar_uso_bano(monto, usuario):
    """
    Registra el uso del baño con el monto entregado.

    Args:
        monto (int | float): Monto del uso de baño.
        usuario (str): Usuario que registra la operación.

    Returns:
        bool: True si el registro fue exitoso, False en caso contrario.
    """
    try:
        with db_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO usos_bano (fecha_hora, monto, usuario)
                VALUES (%s, %s, %s)
            """, (datetime.now(), monto, usuario))
        return True

    except Exception as e:
        print(f"Error al registrar uso de baño: {e}")
        return False


def revertir_en_espera(id_ingreso):
    """
    Revierte el estado 'en espera' de un ingreso activo para volverlo a estado normal.

    Args:
        id_ingreso (int): ID del ingreso a revertir.

    Returns:
        bool: True si fue exitoso, False en caso contrario.
    """
    try:
        with db_cursor(commit=True) as cursor:
            cursor.execute("""
                UPDATE ingresos
                SET en_espera = 0
                WHERE id_ingreso = %s
                  AND fecha_hora_salida IS NULL
            """, (id_ingreso,))
            return cursor.rowcount > 0

    except Exception as e:
        print(f"Error al revertir ingreso en espera: {e}")
        return False


def reingresar_vehiculo_cerrado(
    id_ingreso,
    usuario_reversion,
    confirma_sin_cobro=False,
    motivo="",
    confirma_ticket_impreso=False,
):
    """Revierte una salida sin cobro sobre el mismo ingreso, con auditoría inmutable."""
    motivo = str(motivo or "").strip() or "No informado"
    if not confirma_sin_cobro:
        return False, "Debes confirmar que no se cobró dinero antes de revertir la salida."

    try:
        with db_cursor(dictionary=True, commit=True) as cursor:
            cursor.execute("""
                SELECT i.id_ingreso, i.id_vehiculo, v.patente,
                       i.fecha_hora_ingreso, i.fecha_hora_salida,
                       i.tarifa_aplicada, i.usuario, i.cerrado
                FROM ingresos i
                JOIN vehiculos v ON v.id_vehiculo = i.id_vehiculo
                WHERE i.id_ingreso = %s
                FOR UPDATE
            """, (id_ingreso,))
            ingreso = cursor.fetchone()

            if not ingreso or ingreso["fecha_hora_salida"] is None:
                return False, "El ingreso no tiene una salida reversible."
            if ingreso["cerrado"]:
                return False, "No se puede revertir una salida incluida en un cierre diario."

            cursor.execute("""
                SELECT id_vehiculo
                FROM vehiculos
                WHERE id_vehiculo = %s
                FOR UPDATE
            """, (ingreso["id_vehiculo"],))
            cursor.fetchone()

            cursor.execute("""
                SELECT id_ingreso
                FROM ingresos
                WHERE id_vehiculo = %s
                  AND fecha_hora_salida IS NULL
                FOR UPDATE
            """, (ingreso["id_vehiculo"],))
            if cursor.fetchone():
                return False, "No se puede revertir: el vehículo ya tiene un ingreso activo."

            cursor.execute("""
                SELECT id_print_job, estado
                FROM print_jobs
                WHERE id_ingreso = %s
                  AND tipo = 'TICKET_SALIDA'
                FOR UPDATE
            """, (id_ingreso,))
            jobs_salida = cursor.fetchall()
            if any(job["estado"] == "IMPRIMIENDO" for job in jobs_salida):
                return False, "No se puede revertir mientras se imprime un ticket de salida."
            if any(job["estado"] == "IMPRESO" for job in jobs_salida) and not confirma_ticket_impreso:
                return False, (
                    "El ticket de salida ya fue impreso; se requiere confirmación explícita "
                    "de su entrega antes de revertir."
                )

            resumen_tickets = json.dumps(
                [{"id_print_job": job["id_print_job"], "estado": job["estado"]} for job in jobs_salida],
                ensure_ascii=True,
            )
            cursor.execute("""
                UPDATE print_jobs
                SET estado = 'CANCELADO'
                WHERE id_ingreso = %s
                  AND tipo = 'TICKET_SALIDA'
                  AND estado IN ('PENDIENTE', 'ERROR', 'REVISION_MANUAL')
            """, (id_ingreso,))
            cursor.execute("""
                UPDATE ingresos
                SET fecha_hora_salida = NULL,
                    tarifa_aplicada = NULL,
                    usuario = NULL
                WHERE id_ingreso = %s
                  AND fecha_hora_salida IS NOT NULL
                  AND cerrado = 0
            """, (id_ingreso,))
            if cursor.rowcount != 1:
                raise RuntimeError("La salida cambió antes de poder revertirse.")

            try:
                cursor.execute("""
                    INSERT INTO reversiones_salida (
                        id_ingreso, patente, fecha_hora_ingreso, fecha_hora_salida_original,
                        tarifa_aplicada_original, usuario_salida_original, usuario_reversion,
                        motivo, ticket_estado_resumen, ticket_impreso_confirmado
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    id_ingreso,
                    ingreso["patente"],
                    ingreso["fecha_hora_ingreso"],
                    ingreso["fecha_hora_salida"],
                    ingreso["tarifa_aplicada"],
                    ingreso["usuario"],
                    usuario_reversion,
                    motivo,
                    resumen_tickets,
                    confirma_ticket_impreso,
                ))
            except Exception as exc:
                # Existing Desktop databases may not have received the audit-table migration.
                print(f"[WARN] Salida revertida sin auditoría: {exc}")

        return True, "Salida revertida; el vehículo conserva su hora de ingreso original."

    except Exception as e:
        print(f"Error al revertir salida: {e}")
        return False, "No se pudo revertir la salida; no se aplicaron cambios."


def alternar_estado_espera(patente):
    """
    Alterna el estado de espera del ingreso activo de una patente.

    Prioriza:
    1. revertir un ingreso en espera si existe
    2. en caso contrario, marcar en espera el ingreso activo normal

    Args:
        patente (str): Patente del vehículo.

    Returns:
        tuple[bool, str]: Resultado y mensaje descriptivo.
    """
    try:
        with db_cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT i.id_ingreso
                FROM ingresos i
                JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
                WHERE v.patente = %s
                  AND i.fecha_hora_salida IS NULL
                  AND i.en_espera = 1
                ORDER BY i.fecha_hora_ingreso DESC
                LIMIT 1
            """, (patente,))
            ingreso_espera = cursor.fetchone()

        if ingreso_espera:
            exito = revertir_en_espera(ingreso_espera["id_ingreso"])
            return exito, "Revertido de estado 'en espera'." if exito else "No se pudo revertir."

        exito = marcar_ingreso_en_espera(patente)
        return exito, "Marcado como 'en espera'." if exito else "No se pudo marcar como espera."

    except Exception as e:
        print(f"Error en alternar_estado_espera: {e}")
        return False, str(e)


def obtener_patentes_existentes():
    """
    Obtiene las patentes de vehículos que actualmente tienen un ingreso activo
    (es decir, ingresos sin fecha de salida).

    Returns:
        list[str]: Lista de patentes con ingreso abierto.
    """
    with db_cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT v.patente
            FROM ingresos i
            JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
            WHERE i.fecha_hora_salida IS NULL
            ORDER BY v.patente ASC
        """)
        filas = cursor.fetchall()
        return [f[0] for f in filas]


def eliminar_ingreso_activo_por_patente(patente, usuario):
    """
    Elimina con respaldo el ingreso abierto en espera más reciente de una patente.

    No usa el selector de ingresos activos general, ya que ese selector prioriza
    ingresos normales para las operaciones de salida.

    Args:
        patente (str): Patente del vehículo.
        usuario (str): Usuario que realiza la eliminación.

    Returns:
        tuple[bool, str]: Resultado y mensaje.
    """
    try:
        with db_cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT i.id_ingreso
                FROM ingresos i
                JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
                WHERE v.patente = %s
                  AND i.fecha_hora_salida IS NULL
                  AND i.en_espera = 1
                ORDER BY i.fecha_hora_ingreso DESC, i.id_ingreso DESC
                LIMIT 1
            """, (patente,))
            ingreso = cursor.fetchone()

        if not ingreso:
            return False, "No hay un ingreso abierto en espera para esta patente."

        id_ingreso = ingreso["id_ingreso"]

        return eliminar_ingreso_con_respaldo(id_ingreso, usuario)

    except Exception as e:
        print(f"Error al eliminar ingreso activo por patente: {e}")
        return False, "Ocurrió un error al eliminar el ingreso."
