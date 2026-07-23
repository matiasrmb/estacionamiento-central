import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_FILE_NAME = "desktop.log"
LOG_DIR_NAME = "logs"
MAX_LOG_BYTES = 1_000_000
BACKUP_COUNT = 5
_HANDLER_MARKER = "_estacionamiento_desktop_logging"
_LOG_PATH = None


def _default_base_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent.parent


def _fallback_base_path() -> Path:
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "EstacionamientoCentral"
    return Path.cwd()


def _create_file_handler(base_path: Path) -> tuple[RotatingFileHandler, Path]:
    log_dir = base_path / LOG_DIR_NAME
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / LOG_FILE_NAME

    handler = RotatingFileHandler(
        log_path,
        maxBytes=MAX_LOG_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    return handler, log_path


def setup_logging(base_path=None) -> Path:
    """
    Configure minimal persistent desktop logging.

    The function is idempotent and returns the active log file path. In packaged
    builds it first tries the executable directory and falls back to LOCALAPPDATA
    if the installation directory is not writable.
    """
    global _LOG_PATH

    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if getattr(handler, _HANDLER_MARKER, False):
            return _LOG_PATH or Path(getattr(handler, "baseFilename", ""))

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    base = Path(base_path) if base_path is not None else _default_base_path()

    try:
        file_handler, log_path = _create_file_handler(base)
    except OSError:
        file_handler, log_path = _create_file_handler(_fallback_base_path())

    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    setattr(file_handler, _HANDLER_MARKER, True)
    root_logger.addHandler(file_handler)

    if not getattr(sys, "frozen", False):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        setattr(console_handler, _HANDLER_MARKER, True)
        root_logger.addHandler(console_handler)

    if root_logger.level > logging.INFO:
        root_logger.setLevel(logging.INFO)

    _LOG_PATH = log_path
    return log_path
