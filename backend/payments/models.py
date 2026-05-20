from django.conf import settings
from django.db import models


class PaymentMethod(models.Model):
    class SessionMode(models.TextChoices):
        NONE = "none", "Без сессии"
        PLACEHOLDER = "placeholder", "Локальная сессия"
        REDIRECT = "redirect", "Hosted checkout / redirect"

    code = models.SlugField(max_length=48, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    provider_code = models.SlugField(max_length=48, default="manual")
    session_mode = models.CharField(
        max_length=24, choices=SessionMode.choices, default=SessionMode.NONE
    )
    currency = models.CharField(max_length=3, default="RUB")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(
                fields=["is_active", "sort_order"],
                name="payments_me_active_1d802d_idx",
            ),
            models.Index(
                fields=["provider_code", "session_mode"],
                name="payments_me_prov_mode_idx",
            ),
        ]

    def __str__(self):
        return self.name


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает оплаты"
        SESSION_CREATED = "session_created", "Сессия создана"
        AUTHORIZED = "authorized", "Средства авторизованы"
        SUCCEEDED = "succeeded", "Оплачен"
        FAILED = "failed", "Ошибка оплаты"
        CANCELLED = "cancelled", "Отменен"
        REFUNDED = "refunded", "Возвращен"
        EXPIRED = "expired", "Истек"

    TERMINAL_STATUSES = {
        Status.SUCCEEDED,
        Status.FAILED,
        Status.CANCELLED,
        Status.REFUNDED,
        Status.EXPIRED,
    }
    ALLOWED_TRANSITIONS = {
        Status.PENDING: {
            Status.SESSION_CREATED,
            Status.AUTHORIZED,
            Status.SUCCEEDED,
            Status.FAILED,
            Status.CANCELLED,
            Status.EXPIRED,
        },
        Status.SESSION_CREATED: {
            Status.AUTHORIZED,
            Status.SUCCEEDED,
            Status.FAILED,
            Status.CANCELLED,
            Status.EXPIRED,
        },
        Status.AUTHORIZED: {
            Status.SUCCEEDED,
            Status.FAILED,
            Status.CANCELLED,
            Status.REFUNDED,
            Status.EXPIRED,
        },
        Status.SUCCEEDED: {Status.REFUNDED},
        Status.FAILED: set(),
        Status.CANCELLED: set(),
        Status.REFUNDED: set(),
        Status.EXPIRED: set(),
    }

    order = models.ForeignKey(
        "orders.Order", related_name="payments", on_delete=models.PROTECT
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="payments", on_delete=models.PROTECT
    )
    method = models.ForeignKey(
        PaymentMethod,
        related_name="payments",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    method_code = models.CharField(max_length=48)
    provider_code = models.SlugField(max_length=48, default="manual")
    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.PENDING
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    refunded_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="RUB")
    external_payment_id = models.CharField(max_length=120, blank=True)
    idempotency_key = models.CharField(max_length=120, blank=True)
    session_expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["order", "status"], name="payments_pa_order_6c0b5c_idx"
            ),
            models.Index(fields=["user", "status"], name="payments_pa_user_6b742b_idx"),
            models.Index(
                fields=["idempotency_key"], name="payments_pa_idempo_7b4d67_idx"
            ),
            models.Index(
                fields=["user", "created_at"],
                name="payments_pa_user_created_idx",
            ),
            models.Index(
                fields=["order", "provider_code", "external_payment_id"],
                name="payments_pa_ordprovext_idx",
            ),
            models.Index(
                fields=["provider_code", "status"],
                name="payments_pa_prov_stat_idx",
            ),
            models.Index(
                fields=["method_code"],
                name="payments_pa_method_idx",
            ),
            models.Index(
                fields=["status", "created_at"],
                name="payments_pa_status_created_idx",
            ),
            models.Index(
                fields=["session_expires_at"],
                name="payments_pa_expire_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "idempotency_key"],
                condition=~models.Q(idempotency_key=""),
                name="unique_payment_idempotency_per_user",
            )
        ]

    @property
    def is_terminal(self):
        return self.status in self.TERMINAL_STATUSES

    def can_transition_to(self, new_status):
        return new_status in self.ALLOWED_TRANSITIONS.get(self.status, set())

    def transition_to(
        self,
        new_status,
        *,
        event_type="state_changed",
        message="",
        payload=None,
        external_event_id="",
        save=True,
    ):
        if new_status == self.status:
            return None
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Payment cannot transition from {self.status} to {new_status}."
            )

        previous_status = self.status
        self.status = new_status
        if save:
            self.save(update_fields=["status", "updated_at"])
        return PaymentEvent.objects.create(
            payment=self,
            event_type=event_type,
            previous_status=previous_status,
            new_status=new_status,
            message=message,
            payload=payload or {},
            external_event_id=external_event_id,
        )

    def __str__(self):
        return f"Payment #{self.pk} {self.status}"


class PaymentRefund(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Запрошен"
        SUCCEEDED = "succeeded", "Успешен"
        FAILED = "failed", "Ошибка"

    payment = models.ForeignKey(
        Payment, related_name="refunds", on_delete=models.CASCADE
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="RUB")
    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.REQUESTED
    )
    external_refund_id = models.CharField(max_length=120, blank=True)
    message = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["payment", "created_at"], name="payments_ref_payment_idx"),
            models.Index(fields=["status"], name="payments_ref_status_idx"),
        ]

    def __str__(self):
        return f"Refund {self.amount} {self.currency} for payment #{self.payment_id}"


class PaymentEvent(models.Model):
    payment = models.ForeignKey(
        Payment, related_name="events", on_delete=models.CASCADE
    )
    event_type = models.CharField(max_length=64)
    previous_status = models.CharField(
        max_length=24, choices=Payment.Status.choices, blank=True
    )
    new_status = models.CharField(max_length=24, choices=Payment.Status.choices)
    message = models.CharField(max_length=255, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    external_event_id = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(
                fields=["payment", "created_at"],
                name="payments_ev_payment_2791bc_idx",
            ),
            models.Index(
                fields=["external_event_id"],
                name="payments_ev_externa_69f741_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["payment", "external_event_id"],
                condition=~models.Q(external_event_id=""),
                name="unique_payment_event_external_id",
            )
        ]

    def __str__(self):
        return f"{self.event_type}: {self.previous_status}->{self.new_status}"
