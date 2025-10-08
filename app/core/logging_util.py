"""Logging helpers for the Roboflow Uploader."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .config import APP_NAME, APP_VERSION, APP_BUILD_DATE

APP_LOGGER_NAME = "roboflow_uploader"


class JsonlEventHandler(logging.Handler):
    """A logging handler that writes structured events to a JSONL file."""

    def __init__(self, output_file: Path) -> None:
        super().__init__(level=logging.INFO)
        self.output_file = output_file
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401 - logging API
        event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.args and isinstance(record.args, dict):
            event.update(record.args)
        line = json.dumps(event, ensure_ascii=False)
        with self.output_file.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")


def setup_logging(logs_dir: Path) -> logging.Logger:
    """Configure the application logger and structured event sink."""

    # Create date-based log files for better organization
    today = datetime.now().strftime("%Y-%m-%d")
    app_log = logs_dir / f"app-{today}.log"
    events_log = logs_dir / f"events-{today}.jsonl"
    app_log.parent.mkdir(parents=True, exist_ok=True)
    
    # Also keep a symlink to latest
    latest_app = logs_dir / "app.log"
    latest_events = logs_dir / "events.jsonl"

    logger = logging.getLogger(APP_LOGGER_NAME)
    logger.setLevel(logging.INFO)

    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        file_handler = logging.FileHandler(app_log, encoding="utf-8")
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Create symlink to latest log
        try:
            if latest_app.exists() or latest_app.is_symlink():
                latest_app.unlink()
            latest_app.symlink_to(app_log.name)
        except Exception:
            pass  # Symlink not critical

    if not any(isinstance(h, JsonlEventHandler) for h in logger.handlers):
        json_handler = JsonlEventHandler(events_log)
        logger.addHandler(json_handler)
        
        # Create symlink to latest events
        try:
            if latest_events.exists() or latest_events.is_symlink():
                latest_events.unlink()
            latest_events.symlink_to(events_log.name)
        except Exception:
            pass  # Symlink not critical

    logger.info(
        "%s v%s (build: %s) logger initialized", 
        APP_NAME, APP_VERSION, APP_BUILD_DATE
    )
    return logger


def log_event(logger: logging.Logger, event: str, **payload: Any) -> None:
    """Log a structured event to both human and machine readable sinks."""

    enriched: Dict[str, Any] = {"event": event, **payload}
    logger.info("event=%s %s", event, json.dumps(payload, ensure_ascii=False))
    for handler in logger.handlers:
        if isinstance(handler, JsonlEventHandler):
            record = logging.LogRecord(
                name=logger.name,
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=event,
                args=enriched,
                exc_info=None,
            )
            handler.handle(record)
