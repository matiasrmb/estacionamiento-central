# Performance baseline

Herramientas para medir el rendimiento actual antes de optimizar la aplicación.

Equipo objetivo: AMD E1-2100 APU 1.00GHz con 4GB de RAM. El caso mínimo a validar es más de 50 vehículos estacionados simultáneamente.

## Seguridad

Los comandos de escritura requieren `--allow-app-db-write` para evitar modificar la base por accidente.

El dataset de prueba usa únicamente:

- Patentes con prefijo `PERF`.
- Usuario `PERF_BENCHMARK` para movimientos históricos/baños.

No borra datos reales. El cleanup solo elimina datos con esos marcadores.

## Crear dataset de carga

```bash
python tools/perf_baseline.py seed --vehicles 50 --closed 200 --baths 50 --reset-perf-data --allow-app-db-write
```

Para exigir más carga:

```bash
python tools/perf_baseline.py seed --vehicles 100 --closed 500 --baths 100 --reset-perf-data --allow-app-db-write
```

## Medir baseline

```bash
python tools/perf_baseline.py measure --repeat 5
```

Salida JSON para comparar antes/después:

```bash
python tools/perf_baseline.py measure --repeat 5 --json
```

## Limpiar datos PERF

```bash
python tools/perf_baseline.py cleanup --allow-app-db-write
```

## Qué mirar

Priorizar estos tiempos:

- `obtener_vehiculos_activos`: impacta el listado de vehículos estacionados.
- `obtener_resumen_diario`: impacta el dashboard.
- `obtener_reportes_*`: impacta reportes/cierres.

En el equipo objetivo, el objetivo inicial es que las operaciones frecuentes se mantengan por debajo de 1 segundo con 50 vehículos activos.
