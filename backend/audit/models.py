from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "create", "Create"
        CHANGE = "change", "Change"
        DELETE = "delete", "Delete"
        ADMIN_ACTION = "admin_action", "Admin action"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="audit_logs",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    action = models.CharField(max_length=32, choices=Action.choices)
    app_label = models.CharField(max_length=64)
    model = models.CharField(max_length=64)
    object_id = models.CharField(max_length=128)
    object_repr = models.CharField(max_length=255)
    changes = models.JSONField(default=dict, blank=True)
    snapshot = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    request_path = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["action", "created_at"], name="audit_action_created_idx"
            ),
            models.Index(
                fields=["app_label", "model", "object_id"],
                name="audit_target_idx",
            ),
            models.Index(
                fields=["actor", "created_at"], name="audit_actor_created_idx"
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk and not kwargs.get("force_insert"):
            raise ValidationError("Audit log entries are append-only.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Audit log entries cannot be deleted.")

    def __str__(self):
        return f"{self.action} {self.app_label}.{self.model} #{self.object_id}"
