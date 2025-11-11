from __future__ import annotations

import logging
from typing import Literal, Optional

try:  # pragma: no cover - optional dependency
    import structlog
except ImportError:  # pragma: no cover - optional dependency
    structlog = None


LOG_LEVEL = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]


def setup_logging(level: Optional[str] = None) -> None:
    """
    Configure standard logging and structlog so that all modules emit consistent,
    JSON-like structured events.
    """
    log_level = _coerce_level(level or "INFO")

    if structlog is not None:
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

        structlog.configure(
            processors=processors,
            wrapper_class=structlog.make_filtering_bound_logger(log_level),
            cache_logger_on_first_use=True,
        )

        logging.basicConfig(
            level=log_level,
            format="%(message)s",
        )
    else:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )


def _coerce_level(level: str) -> int:
    try:
        return getattr(logging, level.upper())
    except AttributeError:
        return logging.INFO

class _ShimLogger:
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def __getattr__(self, name):
        attr = getattr(self._logger, name)
        if callable(attr) and name in {"debug", "info", "warning", "error", "exception", "critical", "log"}:

            def wrapper(message="", *args, **kwargs):
                if "message" in kwargs and not message:
                    message = kwargs.pop("message")
                log_kwargs = {}
                for key in ("exc_info", "stack_info", "extra"):
                    if key in kwargs:
                        log_kwargs[key] = kwargs.pop(key)
                if kwargs:
                    tail = ", ".join(f"{key}={value}" for key, value in kwargs.items())
                    message = f"{message} | {tail}".strip()
                return attr(message, *args, **log_kwargs)

            return wrapper
        return attr


def get_logger(name: Optional[str] = None):
    if structlog is not None:
        return structlog.get_logger(name)
    return _ShimLogger(logging.getLogger(name or __name__))


__all__ = ["setup_logging", "get_logger"]

