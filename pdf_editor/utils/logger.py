"""
Centralized logging configuration.

All modules obtain their logger via `get_logger(__name__)` so that log
records carry the originating module name. Logs are written both to the
console (INFO+) and to a rotating file under ~/.pdf_editor/logs (DEBUG+)
so that a user reporting a bug can attach the log file.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_DIR = Path.home() / ".pdf_editor" / "logs"
_LOG_FILE = _LOG_DIR / "pdf_editor.log"

_CONFIGURED = False


def _configure_root_logger() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger("pdf_editor")
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler: friendlier, less verbose
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    # Rotating file handler: full detail, capped at 2MB x 3 backups
    file_handler = RotatingFileHandler(
        _LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    root.addHandler(console_handler)
    root.addHandler(file_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger, configuring handlers on first use."""
    _configure_root_logger()
    return logging.getLogger(f"pdf_editor.{name}")


def log_file_path() -> Path:
    """Expose the log file location (useful for a 'View Logs' menu item)."""
    return _LOG_FILE
