import contextvars
import json
import logging
import re
import time
import uuid


request_id_var = contextvars.ContextVar("request_id", default="-")
correlation_id_var = contextvars.ContextVar("correlation_id", default="-")
user_id_var = contextvars.ContextVar("user_id", default="-")
order_id_var = contextvars.ContextVar("order_id", default="-")

SENSITIVE_LOG_KEYS = {
    "access",
    "access_token",
    "address",
    "admin_notes",
    "authorization",
    "city",
    "email",
    "external_payment_id",
    "first_name",
    "last_name",
    "line1",
    "line2",
    "password",
    "phone",
    "postal_code",
    "refresh",
    "refresh_token",
    "recipient",
    "recipient_name",
    "recipient_phone",
    "secret",
    "signature",
    "shipping_name",
    "shipping_postal_code",
    "shipping_city",
    "shipping_line1",
    "shipping_line2",
    "shipping_phone",
    "token",
}
REDACTED = "[redacted]"
EMAIL_PATTERN = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d[\d\-\s()]{7,}\d)(?!\w)")
SECRET_PATTERN = re.compile(
    r"(?i)\b(access|refresh|token|secret|signature|authorization|password)\b\s*[:=]\s*([^\s,;]+)"
)


def _safe_header_id(value):
    value = (value or "").strip()
    if not value or len(value) > 128:
        return ""
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:")
    if any(char not in allowed for char in value):
        return ""
    return value


def get_log_context():
    return {
        "request_id": request_id_var.get(),
        "correlation_id": correlation_id_var.get(),
        "user_id": user_id_var.get(),
        "order_id": order_id_var.get(),
    }


def bind_log_context(
    *,
    request_id="-",
    correlation_id="-",
    user_id="-",
    order_id="-",
):
    return (
        request_id_var.set(request_id or "-"),
        correlation_id_var.set(correlation_id or "-"),
        user_id_var.set(user_id or "-"),
        order_id_var.set(order_id or "-"),
    )


def reset_log_context(tokens):
    order_id_var.reset(tokens[3])
    user_id_var.reset(tokens[2])
    correlation_id_var.reset(tokens[1])
    request_id_var.reset(tokens[0])


def scrub_log_payload(value):
    if isinstance(value, dict):
        return {
            key: (
                REDACTED
                if str(key).lower() in SENSITIVE_LOG_KEYS
                else scrub_log_payload(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [scrub_log_payload(item) for item in value]
    if isinstance(value, tuple):
        return tuple(scrub_log_payload(item) for item in value)
    return value


def sanitize_log_text(value, *, limit=None):
    if value is None:
        return ""
    text = str(value)
    text = EMAIL_PATTERN.sub(REDACTED, text)
    text = PHONE_PATTERN.sub(REDACTED, text)
    text = SECRET_PATTERN.sub(lambda match: f"{match.group(1)}={REDACTED}", text)
    if limit is not None:
        return text[:limit]
    return text


class RequestContextFilter(logging.Filter):
    def filter(self, record):
        for key, value in get_log_context().items():
            setattr(record, key, value)
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": sanitize_log_text(record.getMessage(), limit=1000),
            "request_id": getattr(record, "request_id", "-"),
            "correlation_id": getattr(record, "correlation_id", "-"),
            "user_id": getattr(record, "user_id", "-"),
            "order_id": getattr(record, "order_id", "-"),
        }
        for field in (
            "method",
            "path",
            "status_code",
            "duration_ms",
            "route",
            "task_id",
            "task_name",
            "exception_type",
        ):
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        for field in ("payload", "metadata", "details"):
            if hasattr(record, field):
                payload[field] = scrub_log_payload(getattr(record, field))
        if record.exc_info:
            payload["exception"] = sanitize_log_text(
                self.formatException(record.exc_info),
                limit=2000,
            )
        return json.dumps(payload, ensure_ascii=False, default=str)


class RequestContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger("animeattire.request")

    def __call__(self, request):
        request_id = (
            _safe_header_id(request.headers.get("X-Request-ID")) or uuid.uuid4().hex
        )
        correlation_id = (
            _safe_header_id(request.headers.get("X-Correlation-ID")) or request_id
        )

        tokens = (
            request_id_var.set(request_id),
            correlation_id_var.set(correlation_id),
            user_id_var.set("-"),
            order_id_var.set("-"),
        )
        request.request_id = request_id
        request.correlation_id = correlation_id
        started_at = time.perf_counter()
        try:
            response = self.get_response(request)
            user = getattr(request, "user", None)
            if getattr(user, "is_authenticated", False):
                user_id_var.set(str(user.pk))
            order_id = self._extract_order_id(request)
            if order_id:
                order_id_var.set(str(order_id))
            self._log_request(request, response, started_at)
            response["X-Request-ID"] = request_id
            response["X-Correlation-ID"] = correlation_id
            return response
        finally:
            order_id_var.reset(tokens[3])
            user_id_var.reset(tokens[2])
            correlation_id_var.reset(tokens[1])
            request_id_var.reset(tokens[0])

    def _extract_order_id(self, request):
        resolver_match = getattr(request, "resolver_match", None)
        if not resolver_match:
            return ""
        route_name = resolver_match.url_name or ""
        if not route_name.startswith("order"):
            return ""
        return resolver_match.kwargs.get("pk") or resolver_match.kwargs.get("id") or ""

    def _log_request(self, request, response, started_at):
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        resolver_match = getattr(request, "resolver_match", None)
        route = resolver_match.url_name if resolver_match else "-"
        self.logger.info(
            "request completed",
            extra={
                "method": request.method,
                "path": request.path_info,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "route": route,
            },
        )
