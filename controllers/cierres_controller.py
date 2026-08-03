"""Soporte de esquema y protección del cierre diario en Desktop."""

import mysql.connector

from controllers.operaciones_servicio_controller import asegurar_schema_operaciones_servicio
from controllers.mensuales_controller import asegurar_schema_mensuales
from utils.db import db_cursor


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
            "ALTER TABLE cierres_diarios ADD COLUMN total_noches INT NOT NULL DEFAULT 0",
            "ALTER TABLE cierres_diarios ADD COLUMN total_noches_monto INT NOT NULL DEFAULT 0",
            "ALTER TABLE usos_bano ADD COLUMN id_cierre INT NULL",
            "ALTER TABLE usos_bano ADD INDEX idx_usos_bano_cierre (id_cierre)",
            "ALTER TABLE operaciones_servicio ADD COLUMN cerrado TINYINT(1) NOT NULL DEFAULT 0",
            "ALTER TABLE operaciones_servicio ADD INDEX idx_operaciones_servicio_cierre (cerrado, estado, fecha_hora_fin)",
        ):
            _ejecutar_schema(cursor, sentencia)

    _SCHEMA_CIERRES_ASEGURADO = True

def realizar_cierre_diario(_usuario):
    """Evita que Desktop cierre directamente sin el bloqueo central de la API."""
    return False, (
        "El cierre diario no está disponible en Desktop. "
        "Realícelo desde Mobile/API."
    )

