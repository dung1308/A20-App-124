"""
utils/logger.py
---------------
Responsibility: Centralised logger factory.

Upgrades over original:
  1. PII MASKING FILTER   — strips emails, phones, CCCD numbers before emission.
  2. JSON HANDLER (prod)  — structured JSON lines when ENVIRONMENT=production,
                            ready for Google Cloud Logging / Datadog ingest.
  3. FILE HANDLER (dev)   — writes to logs/app.log when ENVIRONMENT != production.
  4. TRACE ID INJECTION   — LogRecord gains a `trace_id` field automatically;
                            ObservabilityMiddleware sets it per-request via
                            the `_trace_ctx` context var so every log line
                            emitted during that request carries the same ID.

Usage:
    from utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Message")          # trace_id injected automatically

Trace wiring (done inside ObservabilityMiddleware, not here):
    from utils.logger import set_trace_id, clear_trace_id
    set_trace_id("req-abc-123")
    ...  # all log calls in this thread/task carry trace_id
    clear_trace_id()
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import re
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

ENVIRONMENT  = os.getenv("ENVIRONMENT", "development")   # "production" | "development"
LOG_LEVEL    = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_DIR      = Path(os.getenv("LOG_DIR", "logs"))
LOG_FILE     = LOG_DIR / "app.log"
MAX_BYTES    = 10 * 1024 * 1024   # 10 MB per file
BACKUP_COUNT = 5

# ---------------------------------------------------------------------------
# Trace ID context variable  (one per async task / thread)
# ---------------------------------------------------------------------------

_trace_ctx: ContextVar[str] = ContextVar("trace_id", default="-")


def set_trace_id(trace_id: str) -> None:
    """Call at the start of a request to attach trace_id to all subsequent logs."""
    _trace_ctx.set(trace_id)


def clear_trace_id() -> None:
    """Call at the end of a request to reset the trace context."""
    _trace_ctx.set("-")


def get_trace_id() -> str:
    return _trace_ctx.get()


# ---------------------------------------------------------------------------
# PII masking filter
# ---------------------------------------------------------------------------

_PII_PATTERNS = [
    (re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"), "[EMAIL]"),
    (re.compile(r"\b(\+84|0)(3[2-9]|5[6-9]|7[0|6-9]|8[0-9]|9[0-9])\d{7}\b"), "[PHONE]"),
    (re.compile(r"\b\d{9}(?:\d{3})?\b"), "[ID_NUMBER]"),   # 9 or 12 digit national ID
]


class PIIMaskingFilter(logging.Filter):
    """Scans log message + all extra fields and redacts PII patterns."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._mask(str(record.msg))
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self._mask(str(v)) for k, v in record.args.items()}
            else:
                record.args = tuple(self._mask(str(a)) for a in record.args)
        # Inject trace_id so all formatters can use it
        record.trace_id = get_trace_id()
        return True

    @staticmethod
    def _mask(text: str) -> str:
        for pattern, replacement in _PII_PATTERNS:
            text = pattern.sub(replacement, text)
        return text


# ---------------------------------------------------------------------------
# JSON formatter  (production)
# ---------------------------------------------------------------------------

class JSONFormatter(logging.Formatter):
    """
    Emits one JSON object per line — compatible with Cloud Logging / Datadog.

    Fields: timestamp, severity, logger, trace_id, message, [exc_info]
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity":  record.levelname,
            "logger":    record.name,
            "trace_id":  getattr(record, "trace_id", "-"),
            "message":   record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Plain formatter  (development)
# ---------------------------------------------------------------------------

_PLAIN_FORMAT = (
    "%(asctime)s [%(trace_id)s] %(name)s %(levelname)s — %(message)s"
)


# ---------------------------------------------------------------------------
# Module-level handler registry  (prevents duplicate handlers)
# ---------------------------------------------------------------------------

_configured_loggers: set[str] = set()


# ---------------------------------------------------------------------------
# Public factory
# ---------------------------------------------------------------------------

def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Return a named logger with PII masking, trace ID injection, and
    environment-appropriate handlers.

    Args:
        name:  Module name — pass __name__ from the calling module.
        level: Optional level override (e.g. "DEBUG", "WARNING").
               If None, inherits from LOG_LEVEL env var.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    effective_level = getattr(logging, (level or LOG_LEVEL).upper(), logging.INFO)
    logger.setLevel(effective_level)

    # Attach handlers only once per logger name
    if name not in _configured_loggers:
        _configured_loggers.add(name)
        pii_filter = PIIMaskingFilter()

        if ENVIRONMENT == "production":
            # --- Structured JSON to stdout (Cloud Logging sidecar picks it up) ---
            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setFormatter(JSONFormatter())
            stdout_handler.addFilter(pii_filter)
            logger.addHandler(stdout_handler)

        else:
            # --- Human-readable to stdout ---
            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setFormatter(
                logging.Formatter(_PLAIN_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
            )
            stdout_handler.addFilter(pii_filter)
            logger.addHandler(stdout_handler)

            # --- Rotating file handler for local debugging ---
            try:
                LOG_DIR.mkdir(parents=True, exist_ok=True)
                file_handler = logging.handlers.RotatingFileHandler(
                    LOG_FILE,
                    maxBytes=MAX_BYTES,
                    backupCount=BACKUP_COUNT,
                    encoding="utf-8",
                )
                file_handler.setFormatter(
                    logging.Formatter(_PLAIN_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
                )
                file_handler.addFilter(pii_filter)
                logger.addHandler(file_handler)
            except OSError as exc:
                # Don't crash the app if log dir is not writable
                logger.warning(f"Could not open log file {LOG_FILE}: {exc}")

        # Prevent log records from bubbling to the root logger's handlers
        logger.propagate = False

    return logger