import json
import logging
import re
from datetime import datetime, timezone


_EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_BEARER_PATTERN = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
_CREDENTIAL_PATTERN = re.compile(
    r"(?i)\b(password|secret|token|api[_-]?key|authorization)"
    r"(\s*[:=]\s*)([^,\s;]+)"
)
_URL_CREDENTIAL_PATTERN = re.compile(r"(?i)(https?://)[^/@\s]+:[^/@\s]+@")
_KNOWN_TOKEN_PATTERNS = (
    re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    re.compile(
        r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"
    ),
)


def _redact(value: str) -> str:
    value = _BEARER_PATTERN.sub("Bearer [REDACTED]", value)
    value = _CREDENTIAL_PATTERN.sub(r"\1\2[REDACTED]", value)
    value = _URL_CREDENTIAL_PATTERN.sub(r"\1[REDACTED]@", value)
    for pattern in _KNOWN_TOKEN_PATTERNS:
        value = pattern.sub("[REDACTED_TOKEN]", value)
    return _EMAIL_PATTERN.sub("[REDACTED_EMAIL]", value)


class ProductionJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = _redact(record.getMessage())
        event = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
        }
        if record.exc_info:
            event["exception_type"] = record.exc_info[0].__name__
        return json.dumps(event, separators=(",", ":"))


def configure_production_logging(app) -> None:
    formatter = ProductionJsonFormatter()
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.addHandler(logging.StreamHandler())
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)
    root_logger.setLevel(logging.INFO)

    for handler in app.logger.handlers:
        handler.setFormatter(formatter)
    app.logger.setLevel(logging.INFO)


def init_sentry(app) -> None:
    dsn = app.config.get("SENTRY_DSN")
    if not dsn:
        return

    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.flask import FlaskIntegration

    sentry_sdk.init(
        dsn=dsn,
        integrations=[FlaskIntegration(), CeleryIntegration()],
        send_default_pii=False,
        before_send=_scrub_sentry_event,
    )


def _scrub_sentry_event(event, hint):
    event.pop("extra", None)
    if event.get("message"):
        event["message"] = _redact(str(event["message"]))
    for exception in event.get("exception", {}).get("values", []):
        if exception.get("value"):
            exception["value"] = _redact(str(exception["value"]))
    request = event.get("request")
    if request:
        request.pop("headers", None)
        request.pop("cookies", None)
        request.pop("data", None)
        if "url" in request:
            request["url"] = _redact(str(request["url"]))
    user = event.get("user")
    if user:
        user.pop("email", None)
        user.pop("username", None)
        user.pop("ip_address", None)
    for breadcrumb in event.get("breadcrumbs", {}).get("values", []):
        if breadcrumb.get("message"):
            breadcrumb["message"] = _redact(str(breadcrumb["message"]))
    return event
