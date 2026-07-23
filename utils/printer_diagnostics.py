"""
Helpers for printer support guidance and diagnostics.

These functions do not print. They only format actionable status so the UI can
explain the supported path without promising that unreliable generic drivers
will work.
"""

from __future__ import annotations


SUPPORTED_PRINT_PATH = (
    "Ruta soportada: SumatraPDF + PRINTER_NAME configurado en Windows + "
    "driver térmico validado por el fabricante. No se promete compatibilidad "
    "con drivers térmicos genéricos no validados."
)


def format_ticket_queue_status(status: dict) -> str:
    """Format the in-memory ticket queue status for support/debug UI."""
    submitted = status.get("submitted", 0)
    succeeded = status.get("succeeded", 0)
    failed = status.get("failed", 0)
    message = (
        "Estado de tickets: "
        f"enviados {submitted}, correctos {succeeded}, fallidos {failed}."
    )

    last_failure_description = status.get("last_failure_description")
    last_failure_error = status.get("last_failure_error")
    if last_failure_description or last_failure_error:
        failure_parts = []
        if last_failure_description:
            failure_parts.append(f"último fallo: {last_failure_description}")
        if last_failure_error:
            failure_parts.append(f"error: {last_failure_error}")
        message = f"{message} {'; '.join(failure_parts)}."

    return message


def build_printer_diagnostics(
    *,
    sumatra_path: str,
    sumatra_exists: bool,
    configured_printer: str | None,
    installed_printers: list[str],
    default_printer: str | None,
    queue_count: int | None,
    last_error: str | None,
) -> dict[str, str]:
    """Build a UI-friendly diagnostic summary for ticket printing."""
    messages: list[str] = []
    details: list[str] = []
    status = "PASS"

    if sumatra_path and sumatra_exists:
        details.append(f"SumatraPDF: {sumatra_path}")
    else:
        status = "FAIL"
        messages.append("SUMATRA_PATH no existe o no está configurado")

    printer = (configured_printer or "").strip()
    if not printer:
        status = "FAIL"
        messages.append("PRINTER_NAME no está configurado")
    elif printer not in installed_printers:
        status = "FAIL"
        messages.append("PRINTER_NAME no coincide con una impresora instalada")
    else:
        details.append(f"Impresora configurada: {printer}")

    if default_printer:
        details.append(f"Impresora predeterminada de Windows: {default_printer}")

    if queue_count is not None:
        details.append(f"Trabajos en cola: {queue_count}")

    if last_error:
        details.append(f"Último error visible: {last_error}")

    if not messages:
        messages.append(f"SumatraPDF y la impresora configurada están disponibles: {printer}")

    return {
        "status": status,
        "summary": "; ".join(messages),
        "details": "\n".join(details),
        "guidance": SUPPORTED_PRINT_PATH,
    }
