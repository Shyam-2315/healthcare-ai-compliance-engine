import json
import logging
from datetime import date, datetime, time
from typing import Any

REQUEST_ID_HEADER = "X-Request-ID"
LOGGER_NAME = "app"
_RESERVED = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
    "asctime",
}


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat(timespec="milliseconds") + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in _RESERVED or key.startswith("_"):
                continue
            payload[key] = _json_safe(value)
        return json.dumps(payload, separators=(",", ":"))


def configure_logging(level: str) -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level.upper())
    logger.propagate = True

    if not logger.handlers:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(StructuredFormatter())
        logger.addHandler(stream_handler)
    else:
        for existing_handler in logger.handlers:
            existing_handler.setFormatter(StructuredFormatter())
    return logger


def get_logger(name: str = LOGGER_NAME) -> logging.Logger:
    return logging.getLogger(name)


def log_event(
    logger: logging.Logger,
    level: int,
    message: str,
    **fields: Any,
) -> None:
    logger.log(level, message, extra={key: _json_safe(value) for key, value in fields.items()})


def request_log_fields(
    *,
    request_id: str,
    endpoint: str,
    method: str,
    claim_id: str | None = None,
    status_code: int | None = None,
    processing_time_ms: int | None = None,
    error_code: str | None = None,
    error_type: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "request_id": request_id,
        "endpoint": endpoint,
        "method": method,
    }
    if claim_id:
        fields["claim_id"] = claim_id
    if status_code is not None:
        fields["status_code"] = status_code
    if processing_time_ms is not None:
        fields["processing_time_ms"] = processing_time_ms
    if error_code is not None:
        fields["error_code"] = error_code
    if error_type is not None:
        fields["error_type"] = error_type
    fields.update(extra)
    return fields


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return sorted(_json_safe(item) for item in value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    if isinstance(value, Exception):
        return str(value)
    return value
