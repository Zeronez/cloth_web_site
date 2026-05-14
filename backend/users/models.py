from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    phone = models.CharField(max_length=32, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    account_deleted_at = models.DateTimeField(null=True, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    privacy_policy_accepted_at = models.DateTimeField(null=True, blank=True)
    privacy_policy_version = models.CharField(max_length=32, blank=True)
    offer_agreement_accepted_at = models.DateTimeField(null=True, blank=True)
    offer_agreement_version = models.CharField(max_length=32, blank=True)
    marketing_opt_in_at = models.DateTimeField(null=True, blank=True)
    marketing_opt_in_version = models.CharField(max_length=32, blank=True)

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_email_verified(self):
        return self.email_verified_at is not None

    @property
    def is_account_deleted(self):
        return self.account_deleted_at is not None

    def mark_email_verified(self):
        if self.email_verified_at is None:
            self.email_verified_at = timezone.now()
            self.save(update_fields=["email_verified_at"])

    @property
    def has_accepted_privacy_policy(self):
        return self.privacy_policy_accepted_at is not None

    @property
    def has_accepted_offer_agreement(self):
        return self.offer_agreement_accepted_at is not None

    @property
    def is_marketing_subscribed(self):
        return self.marketing_opt_in_at is not None

    def mark_required_consents_accepted(self, *, privacy_version, offer_version):
        now = timezone.now()
        update_fields = []
        if self.privacy_policy_accepted_at is None:
            self.privacy_policy_accepted_at = now
            update_fields.append("privacy_policy_accepted_at")
        if self.privacy_policy_version != privacy_version:
            self.privacy_policy_version = privacy_version
            update_fields.append("privacy_policy_version")
        if self.offer_agreement_accepted_at is None:
            self.offer_agreement_accepted_at = now
            update_fields.append("offer_agreement_accepted_at")
        if self.offer_agreement_version != offer_version:
            self.offer_agreement_version = offer_version
            update_fields.append("offer_agreement_version")
        if update_fields:
            self.save(update_fields=update_fields)

    def set_marketing_subscription(self, *, subscribed, version):
        update_fields = []
        if subscribed:
            if self.marketing_opt_in_at is None:
                self.marketing_opt_in_at = timezone.now()
                update_fields.append("marketing_opt_in_at")
            if self.marketing_opt_in_version != version:
                self.marketing_opt_in_version = version
                update_fields.append("marketing_opt_in_version")
        else:
            if self.marketing_opt_in_at is not None:
                self.marketing_opt_in_at = None
                update_fields.append("marketing_opt_in_at")
            if self.marketing_opt_in_version:
                self.marketing_opt_in_version = ""
                update_fields.append("marketing_opt_in_version")
        if update_fields:
            self.save(update_fields=update_fields)


class Address(models.Model):
    user = models.ForeignKey(User, related_name="addresses", on_delete=models.CASCADE)
    label = models.CharField(max_length=64, default="Home")
    recipient_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=32)
    country = models.CharField(max_length=80, default="US")
    city = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=32)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "-created_at"]
        indexes = [
            models.Index(
                fields=["user", "is_default", "created_at"],
                name="users_addr_user_def_idx",
            ),
        ]

    def __str__(self):
        return f"{self.recipient_name}, {self.city}"
