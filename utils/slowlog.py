import logging
import os
import time
import configparser
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Mapping


SENSITIVE_KEYS = ("password", "passwd", "pwd", "token", "secret", "key")


def _threshold_ms(name: str, default_ms: int) -> int:
    env_value = os.getenv(name)
    if env_value is None:
        config = configparser.ConfigParser()
        config_path = Path("config.ini")
        if config_path.exists():
            config.read(config_path, encoding="utf-8")
            env_value = config.get("observability", name, fallback=None)
            if env_value is None:
                env_value = config.get("observability", name.lower(), fallback=None)
    try:
        return int(env_value if env_value is not None else default_ms)
    except (TypeError, ValueError):
        return default_ms


def _safe_value(key: str, value: Any) -> str:
    if any(part in key.lower() for part in SENSITIVE_KEYS):
        return "[REDACTED]"
    text = str(value).replace("\r", " ").replace("\n", " ")
    return text[:120]


def log_if_slow(
    logger: logging.Logger,
    *,
    threshold_env: str,
    default_ms: int,
    area: str,
    operation: str,
    duration_ms: float,
    context: Mapping[str, Any] | None = None,
) -> bool:
    threshold = _threshold_ms(threshold_env, default_ms)
    if threshold <= 0 or duration_ms <= threshold:
        return False

    fields = [
        "slow_operation",
        f"area={area}",
        f"operation={operation}",
        f"duration_ms={duration_ms:.2f}",
        f"threshold_ms={threshold}",
    ]
    for key, value in (context or {}).items():
        fields.append(f"{key}={_safe_value(key, value)}")

    logger.warning(" ".join(fields))
    return True


def slow_operation(operation: str, *, default_ms: int = 1000) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            started = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration_ms = (time.perf_counter() - started) * 1000
                log_if_slow(
                    logging.getLogger(func.__module__),
                    threshold_env="SLOW_DESKTOP_MS",
                    default_ms=default_ms,
                    area="desktop",
                    operation=operation,
                    duration_ms=duration_ms,
                    context={"function": func.__name__},
                )

        return wrapper

    return decorator
