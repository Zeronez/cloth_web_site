from http import HTTPStatus

from rest_framework.exceptions import ErrorDetail
from rest_framework.views import exception_handler as drf_exception_handler

from config.logging import get_log_context


DEFAULT_ERROR_MESSAGES = {
    400: "\u041f\u0440\u043e\u0432\u0435\u0440\u044c\u0442\u0435 \u0432\u0432\u0435\u0434\u0435\u043d\u043d\u044b\u0435 \u0434\u0430\u043d\u043d\u044b\u0435.",
    401: "\u041d\u0435\u043e\u0431\u0445\u043e\u0434\u0438\u043c\u0430 \u0430\u0432\u0442\u043e\u0440\u0438\u0437\u0430\u0446\u0438\u044f.",
    403: "\u041d\u0435\u0434\u043e\u0441\u0442\u0430\u0442\u043e\u0447\u043d\u043e \u043f\u0440\u0430\u0432 \u0434\u043b\u044f \u044d\u0442\u043e\u0433\u043e \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u044f.",
    404: "\u0420\u0435\u0441\u0443\u0440\u0441 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.",
    405: "\u041c\u0435\u0442\u043e\u0434 \u0437\u0430\u043f\u0440\u043e\u0441\u0430 \u043d\u0435 \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u0438\u0432\u0430\u0435\u0442\u0441\u044f.",
    406: "\u0417\u0430\u043f\u0440\u043e\u0448\u0435\u043d\u043d\u044b\u0439 \u0444\u043e\u0440\u043c\u0430\u0442 \u043e\u0442\u0432\u0435\u0442\u0430 \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u0435\u043d.",
    409: "\u041a\u043e\u043d\u0444\u043b\u0438\u043a\u0442 \u0441\u043e\u0441\u0442\u043e\u044f\u043d\u0438\u044f.",
    415: "\u0424\u043e\u0440\u043c\u0430\u0442 \u0437\u0430\u043f\u0440\u043e\u0441\u0430 \u043d\u0435 \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u0438\u0432\u0430\u0435\u0442\u0441\u044f.",
    429: "\u0421\u043b\u0438\u0448\u043a\u043e\u043c \u043c\u043d\u043e\u0433\u043e \u0437\u0430\u043f\u0440\u043e\u0441\u043e\u0432. \u041f\u043e\u0432\u0442\u043e\u0440\u0438\u0442\u0435 \u043f\u043e\u0437\u0436\u0435.",
    503: "\u0421\u0435\u0440\u0432\u0438\u0441 \u0432\u0440\u0435\u043c\u0435\u043d\u043d\u043e \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u0435\u043d. \u041f\u043e\u0432\u0442\u043e\u0440\u0438\u0442\u0435 \u043f\u043e\u043f\u044b\u0442\u043a\u0443 \u0447\u0443\u0442\u044c \u043f\u043e\u0437\u0436\u0435.",
    500: "\u0412\u043d\u0443\u0442\u0440\u0435\u043d\u043d\u044f\u044f \u043e\u0448\u0438\u0431\u043a\u0430 \u0441\u0435\u0440\u0432\u0435\u0440\u0430.",
}

DEFAULT_ERROR_CODES = {
    400: "validation_error",
    401: "authentication_required",
    403: "permission_denied",
    404: "not_found",
    405: "method_not_allowed",
    406: "not_acceptable",
    409: "conflict",
    415: "unsupported_media_type",
    429: "throttled",
    503: "service_unavailable",
    500: "server_error",
}

BUSINESS_ERROR_KEYS = {"cart", "payment", "webhook", "order", "delivery"}


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return response

    status_code = response.status_code
    details = normalize_top_level_details(normalize_error_details(response.data))
    business_error = extract_business_error(details)
    detail_error = extract_detail_error(details)

    if business_error:
        code = business_error["code"]
        message = business_error["message"]
    elif detail_error:
        code = detail_error.get("code") or DEFAULT_ERROR_CODES.get(
            status_code, "api_error"
        )
        message = localized_message(status_code, detail_error.get("message"))
    else:
        code = DEFAULT_ERROR_CODES.get(status_code, "api_error")
        message = localized_message(status_code, HTTPStatus(status_code).phrase)

    log_context = get_log_context()
    response.data = {
        "error": {
            "code": code,
            "message": message,
            "status": status_code,
            "details": details,
            "request_id": log_context.get("request_id"),
            "correlation_id": log_context.get("correlation_id"),
        }
    }
    return response


def normalize_error_details(value):
    if isinstance(value, ErrorDetail):
        return {"message": str(value), "code": value.code}
    if isinstance(value, dict):
        normalized = {key: normalize_error_details(item) for key, item in value.items()}
        if "code" in normalized and "message" in normalized:
            code = normalized_leaf_message(normalized["code"])
            message = normalized_leaf_message(normalized["message"])
            if code and message:
                return {"code": code, "message": message}
        return normalized
    if isinstance(value, list):
        return [normalize_error_details(item) for item in value]
    return value


def normalize_top_level_details(details):
    if not isinstance(details, dict):
        return details
    normalized = {}
    for key, value in details.items():
        if (
            key not in BUSINESS_ERROR_KEYS
            and key != "detail"
            and isinstance(value, dict)
            and {"code", "message"}.issubset(value)
        ):
            normalized[key] = [value]
        else:
            normalized[key] = value
    return normalized


def extract_business_error(details):
    if not isinstance(details, dict):
        return None
    for key, value in details.items():
        if key not in BUSINESS_ERROR_KEYS:
            continue
        if not isinstance(value, dict):
            continue
        code = normalized_leaf_message(value.get("code"))
        message = normalized_leaf_message(value.get("message"))
        if code and message:
            return {"code": code, "message": message}
    return None


def extract_detail_error(details):
    if isinstance(details, dict):
        detail = details.get("detail")
        if isinstance(detail, dict):
            return detail
    return None


def localized_message(status_code, fallback_message=None):
    return (
        DEFAULT_ERROR_MESSAGES.get(int(status_code))
        or fallback_message
        or "\u041e\u0448\u0438\u0431\u043a\u0430 API."
    )


def normalized_leaf_message(value):
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and isinstance(value.get("message"), str):
        return value["message"]
    return None
