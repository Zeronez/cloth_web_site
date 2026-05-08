import contextvars
import json
import logging
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
    "authorization",
    "city",
    "email",
    "external_payment_id",
    "line1",
    "line2",
    "password",
    "phone",
    "refresh",
    "refresh_token",
    "secret",
    "signature",
    "shipping_city",
    "shipping_line1",
    "shipping_line2",
    "shipping_phone",
    "token",
}
REDACTED = "[redacted]"


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


def scrub_log_payload(value):
    if isinstance(value, dict):
        return {
            key: REDACTED
            if str(key).lower() in SENSITIVE_LOG_KEYS
            else scrub_log_payload(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [scrub_log_payload(item) for item in value]
    if isinstance(value, tuple):
        return tuple(scrub_log_payload(item) for item in value)
    return value


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
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
            "correlation_id": getattr(record, "correlation_id", "-"),
            "user_id": getattr(record, "user_id", "-"),
            "order_id": getattr(record, "order_id", "-"),
        }
        for field in ("method", "path", "status_code", "duration_ms", "route"):
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
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
