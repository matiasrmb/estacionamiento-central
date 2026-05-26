"""
Baseline performance tooling for low-end deployment targets.

This script is intentionally outside the application runtime. It creates
realistic benchmark data with a PERF-prefixed marker and measures the current
controller paths without changing production logic.

Examples:
    python tools/perf_baseline.py seed --vehicles 50 --closed 200 --baths 50 --reset-perf-data --allow-app-db-write
    python tools/perf_baseline.py measure --repeat 5
    python tools/perf_baseline.py cleanup --allow-app-db-write
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import tracemalloc
from datetime import date, datetime, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controllers.dashboard_controller import obtener_resumen_banos, obtener_resumen_diario
from controllers.registro_controller import obtener_patentes_existentes, obtener_vehiculos_activos
from controllers.reportes_controller import obtener_reportes
from utils.db import get_connection


PERF_PREFIX = "PERF"
PERF_USER = "PERF_BENCHMARK"


def connect_or_exit():
    conn = get_connection()
    if conn is None:
        raise SystemExit("No se pudo abrir conexión. Revisá config.ini y MySQL.")
    return conn


def require_write_confirmation(args):
    if not args.allow_app_db_write:
        raise SystemExit(
            "Operación cancelada: seed/cleanup modifica la base configurada en config.ini.\n"
            "Si estás usando una base de prueba, repetí el comando con --allow-app-db-write.\n"
            "El script solo toca patentes PERF% y usos de baño del usuario PERF_BENCHMARK."
        )


def cleanup_perf_data(conn):
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            DELETE i
            FROM ingresos i
            JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
            WHERE v.patente LIKE %s
            """,
            (f"{PERF_PREFIX}%",),
        )
        cursor.execute("DELETE FROM vehiculos WHERE patente LIKE %s", (f"{PERF_PREFIX}%",))
        cursor.execute("DELETE FROM usos_bano WHERE usuario = %s", (PERF_USER,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def seed_perf_data(args):
    require_write_confirmation(args)
    conn = connect_or_exit()
    cursor = conn.cursor()
    now = datetime.now().replace(second=0, microsecond=0)

    try:
        if args.reset_perf_data:
            cursor.close()
            cleanup_perf_data(conn)
            cursor = conn.cursor()

        vehicle_ids = []
        for number in range(1, args.vehicles + 1):
            patente = f"{PERF_PREFIX}{number:04d}"
            cursor.execute(
                """
                INSERT INTO vehiculos (patente, tipo_cliente, activo)
                VALUES (%s, 'ocasional', 1)
                ON DUPLICATE KEY UPDATE activo = VALUES(activo)
                """,
                (patente,),
            )
            cursor.execute("SELECT id_vehiculo FROM vehiculos WHERE patente = %s", (patente,))
            vehicle_ids.append(cursor.fetchone()[0])

        for index, vehicle_id in enumerate(vehicle_ids):
            ingreso = now - timedelta(minutes=5 + (index * 7) % 480)
            cursor.execute(
                """
                INSERT INTO ingresos (id_vehiculo, fecha_hora_ingreso, fecha_hora_salida, en_espera, cerrado)
                VALUES (%s, %s, NULL, %s, 0)
                """,
                (vehicle_id, ingreso, 1 if index % 17 == 0 else 0),
            )

        for index in range(args.closed):
            vehicle_id = vehicle_ids[index % len(vehicle_ids)]
            salida = now - timedelta(hours=2 + index)
            ingreso = salida - timedelta(minutes=20 + (index * 11) % 360)
            tarifa = 300 + ((index % 8) * 200)
            cursor.execute(
                """
                INSERT INTO ingresos (
                    id_vehiculo, fecha_hora_ingreso, fecha_hora_salida,
                    tarifa_aplicada, en_espera, cerrado, usuario
                )
                VALUES (%s, %s, %s, %s, 0, 0, %s)
                """,
                (vehicle_id, ingreso, salida, tarifa, PERF_USER),
            )

        for index in range(args.baths):
            cursor.execute(
                """
                INSERT INTO usos_bano (fecha_hora, monto, usuario)
                VALUES (%s, %s, %s)
                """,
                (now - timedelta(minutes=index * 13), 200, PERF_USER),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

    print(
        f"Dataset PERF creado: {args.vehicles} vehículos activos, "
        f"{args.closed} salidas históricas, {args.baths} baños."
    )


def time_call(label, func, repeat):
    samples = []
    last_result = None
    for _ in range(repeat):
        started = time.perf_counter()
        last_result = func()
        samples.append((time.perf_counter() - started) * 1000)

    size = len(last_result) if hasattr(last_result, "__len__") else None
    return {
        "label": label,
        "runs": repeat,
        "min_ms": round(min(samples), 2),
        "avg_ms": round(statistics.mean(samples), 2),
        "max_ms": round(max(samples), 2),
        "items": size,
    }


def measure_baseline(args):
    today = date.today()
    start = today - timedelta(days=args.report_days)

    tracemalloc.start()
    measurements = [
        time_call("obtener_vehiculos_activos", obtener_vehiculos_activos, args.repeat),
        time_call("obtener_patentes_existentes", obtener_patentes_existentes, args.repeat),
        time_call("obtener_resumen_diario", obtener_resumen_diario, args.repeat),
        time_call("obtener_resumen_banos", obtener_resumen_banos, args.repeat),
        time_call(
            f"obtener_reportes_{args.report_days}_dias",
            lambda: obtener_reportes(start, today),
            args.repeat,
        ),
    ]
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    result = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "repeat": args.repeat,
        "python_alloc_current_kb": round(current / 1024, 1),
        "python_alloc_peak_kb": round(peak / 1024, 1),
        "measurements": measurements,
    }

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    print("Baseline de performance")
    print(f"Fecha: {result['timestamp']}")
    print(f"Memoria Python pico aproximada: {result['python_alloc_peak_kb']} KB")
    for item in measurements:
        print(
            f"- {item['label']}: avg={item['avg_ms']} ms "
            f"min={item['min_ms']} ms max={item['max_ms']} ms items={item['items']}"
        )


def run_cleanup(args):
    require_write_confirmation(args)
    conn = connect_or_exit()
    try:
        cleanup_perf_data(conn)
    finally:
        conn.close()
    print("Datos PERF eliminados.")


def main():
    parser = argparse.ArgumentParser(description="Herramientas de baseline de performance.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    seed = subparsers.add_parser("seed", help="Crea dataset PERF para pruebas de carga.")
    seed.add_argument("--vehicles", type=int, default=50)
    seed.add_argument("--closed", type=int, default=200)
    seed.add_argument("--baths", type=int, default=50)
    seed.add_argument("--reset-perf-data", action="store_true")
    seed.add_argument("--allow-app-db-write", action="store_true")
    seed.set_defaults(func=seed_perf_data)

    measure = subparsers.add_parser("measure", help="Mide tiempos de paths frecuentes.")
    measure.add_argument("--repeat", type=int, default=5)
    measure.add_argument("--report-days", type=int, default=7)
    measure.add_argument("--json", action="store_true")
    measure.set_defaults(func=measure_baseline)

    cleanup = subparsers.add_parser("cleanup", help="Elimina solo datos PERF del benchmark.")
    cleanup.add_argument("--allow-app-db-write", action="store_true")
    cleanup.set_defaults(func=run_cleanup)

    args = parser.parse_args()

    if getattr(args, "vehicles", 1) < 1:
        raise SystemExit("--vehicles debe ser mayor que cero.")
    if getattr(args, "repeat", 1) < 1:
        raise SystemExit("--repeat debe ser mayor que cero.")

    args.func(args)


if __name__ == "__main__":
    main()
