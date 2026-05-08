from audit.models import AuditLog
from audit.services import log_admin_event, model_changes, model_snapshot


class AuditedModelAdminMixin:
    audit_snapshot_fields = None

    def save_model(self, request, obj, form, change):
        old_obj = None
        changed_fields = list(getattr(form, "changed_data", []) or [])
        if change and obj.pk and changed_fields:
            old_obj = type(obj).objects.get(pk=obj.pk)

        super().save_model(request, obj, form, change)

        if change:
            if not old_obj or not changed_fields:
                return
            changes = model_changes(old_obj, obj, changed_fields)
            if changes:
                log_admin_event(
                    actor=request.user,
                    action=AuditLog.Action.CHANGE,
                    obj=obj,
                    request=request,
                    changes=changes,
                )
            return

        log_admin_event(
            actor=request.user,
            action=AuditLog.Action.CREATE,
            obj=obj,
            request=request,
            snapshot=model_snapshot(obj, self.audit_snapshot_fields),
        )

    def delete_model(self, request, obj):
        snapshot = model_snapshot(obj, self.audit_snapshot_fields)
        log_admin_event(
            actor=request.user,
            action=AuditLog.Action.DELETE,
            obj=obj,
            request=request,
            snapshot=snapshot,
        )
        super().delete_model(request, obj)
