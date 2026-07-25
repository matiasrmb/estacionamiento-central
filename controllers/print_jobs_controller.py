"""Operaciones administrativas para trabajos de impresion durables."""

from utils.db import db_cursor


def listar_trabajos_impresion_fallidos():
    """Retorna solo los trabajos de impresion que requieren recuperacion."""
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(
            """
            SELECT
                id_print_job AS id,
                tipo,
                destino,
                patente,
                estado,
                intentos,
                max_intentos,
                last_error,
                created_at,
                updated_at
            FROM print_jobs
            WHERE estado IN (%s, %s)
            ORDER BY updated_at DESC, id_print_job DESC
            """,
            ("ERROR", "REVISION_MANUAL"),
        )
        return cursor.fetchall()


def reintentar_trabajo_impresion_fallido(id_print_job):
    """Devuelve un trabajo ERROR a PENDIENTE si sigue siendo recuperable."""
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE print_jobs
            SET
                estado = %s,
                locked_at = NULL,
                locked_by = NULL,
                last_error = NULL,
                next_retry_at = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id_print_job = %s AND estado = %s
            """,
            ("PENDIENTE", id_print_job, "ERROR"),
        )
        return cursor.rowcount == 1


def reintentar_trabajo_impresion_revision_manual(id_print_job):
    """Devuelve un trabajo revisado manualmente a PENDIENTE."""
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE print_jobs
            SET
                estado = %s,
                intentos = 0,
                locked_at = NULL,
                locked_by = NULL,
                last_error = NULL,
                next_retry_at = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id_print_job = %s AND estado = %s
            """,
            ("PENDIENTE", id_print_job, "REVISION_MANUAL"),
        )
        return cursor.rowcount == 1
