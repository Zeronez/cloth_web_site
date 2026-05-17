import hashlib
import hmac
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import Throttled


def _normalize(value):
    return str(value or "").strip().lower()


def _request_ip(request):
    return request.META.get("REMOTE_ADDR", "")


def _hashed_identifier(value):
    normalized = _normalize(value)
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        normalized.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _cache_key(scope, *parts):
    rendered = ":".join(_normalize(part) for part in parts if part is not None)
    return f"auth-security:{scope}:{_hashed_identifier(rendered)}"


def _read_counter(key):
    value = cache.get(key)
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _bump_counter(key, ttl_seconds):
    if cache.add(key, 1, timeout=ttl_seconds):
        return 1
    try:
        return cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=ttl_seconds)
        return 1


def _ensure_not_locked(key, limit):
    if _read_counter(key) >= limit:
        raise Throttled()


@dataclass(frozen=True)
class LoginBuckets:
    per_ip_key: str
    per_account_key: str


def login_buckets(request, username):
    normalized_username = username or "<blank>"
    ip = _request_ip(request)
    return LoginBuckets(
        per_ip_key=_cache_key("login-ip", normalized_username, ip),
        per_account_key=_cache_key("login-account", normalized_username),
    )


def ensure_login_allowed(request, username):
    buckets = login_buckets(request, username)
    _ensure_not_locked(buckets.per_ip_key, settings.AUTH_LOGIN_FAILURE_IP_LIMIT)
    _ensure_not_locked(
        buckets.per_account_key,
        settings.AUTH_LOGIN_FAILURE_ACCOUNT_LIMIT,
    )


def record_login_failure(request, username):
    buckets = login_buckets(request, username)
    _bump_counter(
        buckets.per_ip_key,
        settings.AUTH_LOGIN_FAILURE_WINDOW_SECONDS,
    )
    _bump_counter(
        buckets.per_account_key,
        settings.AUTH_LOGIN_FAILURE_WINDOW_SECONDS,
    )


def clear_login_failures(request, username):
    buckets = login_buckets(request, username)
    cache.delete_many([buckets.per_ip_key, buckets.per_account_key])


def password_reset_request_key(email):
    return _cache_key("password-reset-request", email or "<blank>")


def should_suppress_password_reset_request(email):
    return _read_counter(password_reset_request_key(email)) >= (
        settings.AUTH_PASSWORD_RESET_REQUEST_LIMIT
    )


def record_password_reset_request(email):
    _bump_counter(
        password_reset_request_key(email),
        settings.AUTH_PASSWORD_RESET_REQUEST_WINDOW_SECONDS,
    )


def password_reset_confirm_key(request, uid):
    return _cache_key("password-reset-confirm", uid or "<blank>", _request_ip(request))


def ensure_password_reset_confirm_allowed(request, uid):
    _ensure_not_locked(
        password_reset_confirm_key(request, uid),
        settings.AUTH_PASSWORD_RESET_CONFIRM_LIMIT,
    )


def record_password_reset_confirm_failure(request, uid):
    _bump_counter(
        password_reset_confirm_key(request, uid),
        settings.AUTH_PASSWORD_RESET_CONFIRM_WINDOW_SECONDS,
    )


def clear_password_reset_confirm_failures(request, uid):
    cache.delete(password_reset_confirm_key(request, uid))
