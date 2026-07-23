"""Small background queue for ticket generation and printing jobs."""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor


logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ticket-worker")
_status_lock = threading.Lock()
_ticket_queue_status = {
    "last_submitted_description": None,
    "last_started_description": None,
    "last_success_description": None,
    "last_failure_description": None,
    "last_failure_error": None,
    "submitted": 0,
    "succeeded": 0,
    "failed": 0,
}


def get_ticket_queue_status():
    """Return a snapshot of the in-memory ticket queue status."""
    with _status_lock:
        return dict(_ticket_queue_status)


def reset_ticket_queue_status():
    """Reset queue status counters and last job details for tests."""
    with _status_lock:
        _ticket_queue_status.update({
            "last_submitted_description": None,
            "last_started_description": None,
            "last_success_description": None,
            "last_failure_description": None,
            "last_failure_error": None,
            "submitted": 0,
            "succeeded": 0,
            "failed": 0,
        })


def enqueue_ticket_job(description, func, *args, **kwargs):
    """Submit a ticket job without blocking the operational controller path."""
    with _status_lock:
        _ticket_queue_status["last_submitted_description"] = description
        _ticket_queue_status["submitted"] += 1

    try:
        return _executor.submit(_run_ticket_job, description, func, args, kwargs)
    except Exception:
        logger.exception("Could not enqueue ticket job: %s", description)
        raise


def _run_ticket_job(description, func, args, kwargs):
    with _status_lock:
        _ticket_queue_status["last_started_description"] = description

    try:
        result = func(*args, **kwargs)
        with _status_lock:
            _ticket_queue_status["last_success_description"] = description
            _ticket_queue_status["succeeded"] += 1
        return result
    except Exception as exc:
        with _status_lock:
            _ticket_queue_status["last_failure_description"] = description
            _ticket_queue_status["last_failure_error"] = str(exc)
            _ticket_queue_status["failed"] += 1
        logger.exception("Ticket job failed: %s", description)
        return None
