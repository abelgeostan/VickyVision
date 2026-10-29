import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class StructuredJsonFormatter(logging.Formatter):
    """
    Structured JSON log formatter for VICKY OS.
    Standardizes log fields for high observability across long-running agents.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "component": getattr(record, "component", record.name),
            "agent": getattr(record, "agent", None),
            "task": getattr(record, "task", None),
            "event": getattr(record, "event", None),
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


class StandardStructuredFormatter(logging.Formatter):
    """
    Human-readable structured console formatter with clear contextual tags.
    """
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        component = getattr(record, "component", record.name)
        agent = getattr(record, "agent", "-")
        task = getattr(record, "task", "-")
        event = getattr(record, "event", "-")
        
        ctx_parts = []
        if agent and agent != "-":
            ctx_parts.append(f"agent={agent}")
        if task and task != "-":
            ctx_parts.append(f"task={task}")
        if event and event != "-":
            ctx_parts.append(f"event={event}")
        ctx_str = f" [{', '.join(ctx_parts)}]" if ctx_parts else ""

        base = f"[{timestamp}] [{record.levelname:<5}] [{component}]{ctx_str} {record.getMessage()}"
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


def setup_logging(log_level: str = "INFO", json_format: bool = False) -> None:
    root_logger = logging.getLogger()
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers on re-initialization
    if root_logger.handlers:
        root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if json_format:
        handler.setFormatter(StructuredJsonFormatter())
    else:
        handler.setFormatter(StandardStructuredFormatter())

    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
