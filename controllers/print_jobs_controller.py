"""Operaciones administrativas para trabajos de impresion durables."""

from uuid import uuid4

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


def listar_trabajos_impresion_impresos(limite=50):
    """Retorna trabajos impresos recientes sin exponer su payload."""
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(
            """
            SELECT
                id_print_job AS id,
                tipo,
                destino,
                patente,
                estado,
                created_at,
                updated_at
            FROM print_jobs
            WHERE estado = %s
            ORDER BY updated_at DESC, id_print_job DESC
            LIMIT %s
            """,
            ("IMPRESO", limite),
        )
        return cursor.fetchall()


def crear_reimpresion_trabajo_impresion(id_print_job, operador, motivo):
    """Crea una copia pendiente de un trabajo impreso y deja su auditoria."""
    operador = (operador or "").strip()
    motivo = (motivo or "").strip()
    if not operador:
        raise ValueError("El operador es obligatorio para reimprimir.")
    if not motivo:
        raise ValueError("El motivo de reimpresion es obligatorio.")

    with db_cursor(dictionary=True, commit=True) as cursor:
        cursor.execute(
            """
            SELECT id_print_job, tipo, destino, id_ingreso, patente, payload_json
            FROM print_jobs
            WHERE id_print_job = %s AND estado = %s
            FOR UPDATE
            """,
            (id_print_job, "IMPRESO"),
        )
        source_job = cursor.fetchone()
        if source_job is None:
            return None

        cursor.execute(
            """
            SELECT reprint.new_print_job_id
            FROM print_job_reprints AS reprint
            INNER JOIN print_jobs AS reprint_job
                ON reprint_job.id_print_job = reprint.new_print_job_id
            WHERE reprint.source_print_job_id = %s
              AND reprint_job.estado IN (%s, %s, %s)
            LIMIT 1
            """,
            (source_job["id_print_job"], "PENDIENTE", "IMPRIMIENDO", "REVISION_MANUAL"),
        )
        if cursor.fetchone() is not None:
            return False

        idempotency_key = f"reprint:{source_job['id_print_job']}:{uuid4().hex}"
        cursor.execute(
            """
            INSERT INTO print_jobs
                (tipo, destino, id_ingreso, patente, payload_json, estado, idempotency_key)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                source_job["tipo"],
                source_job["destino"],
                source_job["id_ingreso"],
                source_job["patente"],
                source_job["payload_json"],
                "PENDIENTE",
                idempotency_key,
            ),
        )
        new_print_job_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO print_job_reprints
                (source_print_job_id, new_print_job_id, operator_user, reason)
            VALUES (%s, %s, %s, %s)
            """,
            (source_job["id_print_job"], new_print_job_id, operador, motivo),
        )
        return {"new_print_job_id": new_print_job_id, "audit_id": cursor.lastrowid}


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
