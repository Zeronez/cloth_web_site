import os
import logging

from celery import Celery
from celery.signals import before_task_publish, task_failure, task_postrun, task_prerun

from config.logging import (
    _safe_header_id,
    bind_log_context,
    get_log_context,
    reset_log_context,
)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("animeattire")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

logger = logging.getLogger("animeattire.celery")
TASK_CONTEXT_HEADER = "animeattire_log_context"


def _clean_context_value(value):
    if value in {None, "", "-"}:
        return "-"
    if isinstance(value, str):
        return _safe_header_id(value) or "-"
    return str(value)


def _serialize_task_log_context():
    context = get_log_context()
    return {
        "request_id": _clean_context_value(context.get("request_id")),
        "correlation_id": _clean_context_value(context.get("correlation_id")),
        "user_id": _clean_context_value(context.get("user_id")),
        "order_id": _clean_context_value(context.get("order_id")),
    }


def _extract_task_log_context(headers):
    headers = headers or {}
    context = headers.get(TASK_CONTEXT_HEADER, {})
    if not isinstance(context, dict):
        context = {}
    return {
        "request_id": _clean_context_value(context.get("request_id")),
        "correlation_id": _clean_context_value(context.get("correlation_id")),
        "user_id": _clean_context_value(context.get("user_id")),
        "order_id": _clean_context_value(context.get("order_id")),
    }


@before_task_publish.connect
def inject_task_log_context(headers=None, **kwargs):
    if headers is None:
        return
    headers[TASK_CONTEXT_HEADER] = _serialize_task_log_context()


@task_prerun.connect
def bind_task_log_context(task=None, **kwargs):
    if task is None:
        return
    headers = getattr(task.request, "headers", None) or {}
    context = _extract_task_log_context(headers)
    tokens = bind_log_context(**context)
    setattr(task.request, "_animeattire_log_context_tokens", tokens)


@task_postrun.connect
def clear_task_log_context(task=None, **kwargs):
    if task is None:
        return
    tokens = getattr(task.request, "_animeattire_log_context_tokens", None)
    if tokens is not None:
        reset_log_context(tokens)
        delattr(task.request, "_animeattire_log_context_tokens")


@task_failure.connect
def log_task_failure(
    task_id=None,
    exception=None,
    sender=None,
    args=None,
    kwargs=None,
    traceback=None,
    einfo=None,
    **rest,
):
    task_name = getattr(sender, "name", rest.get("task_name", "unknown"))
    logger.error(
        "celery task failed",
        extra={
            "task_name": task_name,
            "task_id": task_id or "-",
        },
        exc_info=(
            (
                type(exception),
                exception,
                getattr(einfo, "tb", traceback),
            )
            if exception is not None
            else None
        ),
    )
