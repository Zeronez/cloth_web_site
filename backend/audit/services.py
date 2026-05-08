from decimal import Decimal

from django.db.models import Model

from audit.models import AuditLog


REDACTED = "[redacted]"
SENSITIVE_TOKENS = (
    "password",
    "token",
    "secret",
    "key",
    "signature",
    "phone",
    "email",
    "address",
    "line1",
    "line2",
    "postal",
    "note",
)


def is_sensitive_field(field_name):
    normalized = field_name.lower()
    return any(token in normalized for token in SENSITIVE_TOKENS)


def safe_value(field_name, value):
    if is_sensitive_field(field_name):
        return REDACTED
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, Model):
        return str(value.pk)
    return str(value)


def model_identity(obj):
    meta = obj._meta
    return {
        "app_label": meta.app_label,
        "model": meta.model_name,
        "object_id": str(obj.pk or ""),
        "object_repr": str(obj)[:255],
    }


def model_snapshot(obj, fields=None):
    selected_fields = fields or [
        field.name
        for field in obj._meta.fields
        if not field.many_to_many and not field.one_to_many
    ]
    return {
        field_name: safe_value(field_name, getattr(obj, field_name, None))
        for field_name in selected_fields
    }


def model_changes(old_obj, new_obj, field_names):
    changes = {}
    for field_name in field_names:
        old_value = getattr(old_obj, field_name, None)
        new_value = getattr(new_obj, field_name, None)
        if old_value != new_value:
            changes[field_name] = {
                "old": safe_value(field_name, old_value),
                "new": safe_value(field_name, new_value),
            }
    return changes


def request_metadata(request):
    if request is None:
        return {"request_path": "", "ip_address": None, "user_agent": ""}
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    ip_address = forwarded_for.split(",")[0].strip() or request.META.get("REMOTE_ADDR")
    return {
        "request_path": request.path[:255],
        "ip_address": ip_address,
        "user_agent": request.META.get("HTTP_USER_AGENT", "")[:255],
    }


def log_admin_event(
    *,
    actor,
    action,
    obj,
    request=None,
    changes=None,
    snapshot=None,
    metadata=None,
):
    identity = model_identity(obj)
    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        **identity,
        changes=changes or {},
        snapshot=snapshot or {},
        metadata=metadata or {},
        **request_metadata(request),
    )
