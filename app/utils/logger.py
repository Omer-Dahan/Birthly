from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path

import structlog

from app.config import settings


def setup_logging() -> None:
    """Configure structlog + stdlib logging per SPEC chapter 25.

    Two sinks: JSON to a rotating file under ``log_dir``, plain text to stdout
    (picked up by journald under systemd).
    """
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "bot.log",
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter("%(message)s"))

    stdout_stream = sys.stdout
    if hasattr(stdout_stream, "reconfigure"):
        stdout_stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    stdout_handler = logging.StreamHandler(stdout_stream)
    stdout_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(stdout_handler)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
