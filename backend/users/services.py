from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from cart.models import Cart
from cart.serializers import CartSerializer
from favorites.models import FavoriteProduct
from favorites.serializers import FavoriteProductSerializer
from notifications.models import NotificationLog
from orders.models import Order
from orders.serializers import OrderSerializer
from payments.models import Payment
from payments.serializers import PaymentSerializer
from support.models import ContactRequest
from support.serializers import ContactRequestSerializer
from users.models import Address
from users.serializers import AddressSerializer, UserSerializer


User = get_user_model()

ACCOUNT_DELETED_SUPPORT_NAME = "Deleted user"
ACCOUNT_DELETED_SUPPORT_MESSAGE = "Content removed after account deletion request."


def _account_error(code, message):
    raise ValidationError({"account": {"code": code, "message": message}})


def build_account_export_payload(*, user, serializer_context):
    profile = UserSerializer(user, context=serializer_context).data
    addresses = AddressSerializer(
        Address.objects.filter(user=user),
        many=True,
        context=serializer_context,
    ).data
    favorites = FavoriteProductSerializer(
        FavoriteProduct.objects.filter(user=user)
        .select_related("product", "product__category", "product__franchise")
        .prefetch_related("product__images", "product__variants"),
        many=True,
        context=serializer_context,
    ).data
    orders = OrderSerializer(
        Order.objects.filter(user=user)
        .select_related("delivery_snapshot")
        .prefetch_related("items__variant", "delivery_snapshot__tracking_events"),
        many=True,
        context=serializer_context,
    ).data
    payments = PaymentSerializer(
        Payment.objects.filter(user=user)
        .select_related("order", "method")
        .prefetch_related("events"),
        many=True,
        context=serializer_context,
    ).data
    notifications = [
        {
            "id": notification.id,
            "order_id": notification.order_id,
            "notification_type": notification.notification_type,
            "channel": notification.channel,
            "status": notification.status,
            "recipient": notification.recipient,
            "subject": notification.subject,
            "body": notification.body,
            "error_message": notification.error_message,
            "delivered_at": (
                notification.delivered_at.isoformat()
                if notification.delivered_at
                else None
            ),
            "created_at": notification.created_at.isoformat(),
            "updated_at": notification.updated_at.isoformat(),
            "attempts": [
                {
                    "id": attempt.id,
                    "status": attempt.status,
                    "provider_message_id": attempt.provider_message_id,
                    "error_message": attempt.error_message,
                    "created_at": attempt.created_at.isoformat(),
                }
                for attempt in notification.attempts.all()
            ],
        }
        for notification in NotificationLog.objects.filter(order__user=user)
        .prefetch_related("attempts")
        .order_by("-created_at")
    ]
    contact_requests = ContactRequestSerializer(
        ContactRequest.objects.filter(user=user),
        many=True,
        context=serializer_context,
    ).data
    cart = (
        Cart.objects.filter(user=user)
        .prefetch_related("items__variant__product")
        .first()
    )

    return {
        "exported_at": timezone.now().isoformat(),
        "profile": profile,
        "addresses": addresses,
        "favorites": favorites,
        "cart": CartSerializer(cart, context=serializer_context).data if cart else None,
        "orders": orders,
        "payments": payments,
        "notifications": notifications,
        "contact_requests": contact_requests,
    }


@transaction.atomic
def delete_customer_account(*, user):
    locked_user = User.objects.select_for_update().get(pk=user.pk)
    if locked_user.is_staff or locked_user.is_superuser:
        _account_error(
            "staff_account_deletion_disabled",
            "Staff account deletion must be handled by operators.",
        )
    if locked_user.orders.exclude(status__in=Order.TERMINAL_STATUSES).exists():
        _account_error(
            "open_orders_block_account_deletion",
            "Complete or cancel active orders before deleting the account.",
        )
    if locked_user.is_account_deleted:
        _account_error(
            "account_already_deleted",
            "This account was already deleted.",
        )

    original_email = locked_user.email
    if locked_user.avatar:
        locked_user.avatar.delete(save=False)

    Address.objects.filter(user=locked_user).delete()
    FavoriteProduct.objects.filter(user=locked_user).delete()
    Cart.objects.filter(user=locked_user).delete()

    ContactRequest.objects.filter(user=locked_user).update(
        user=None,
        name=ACCOUNT_DELETED_SUPPORT_NAME,
        email=f"deleted-user-{locked_user.pk}@example.invalid",
        phone="",
        message=ACCOUNT_DELETED_SUPPORT_MESSAGE,
        ip_address=None,
        user_agent="",
        updated_at=timezone.now(),
    )
    NotificationLog.objects.filter(order__user=locked_user).update(
        recipient=f"deleted-user-{locked_user.pk}@example.invalid",
        subject="Deleted account notification record",
        body=ACCOUNT_DELETED_SUPPORT_MESSAGE,
        error_message="",
        updated_at=timezone.now(),
    )

    locked_user.set_unusable_password()
    locked_user.username = f"deleted-user-{locked_user.pk}"
    locked_user.email = ""
    locked_user.first_name = ""
    locked_user.last_name = ""
    locked_user.phone = ""
    locked_user.avatar = ""
    locked_user.fit_profile = {}
    locked_user.fit_profile_updated_at = None
    locked_user.is_active = False
    locked_user.account_deleted_at = timezone.now()
    locked_user.marketing_opt_in_at = None
    locked_user.marketing_opt_in_version = ""
    locked_user.save(
        update_fields=[
            "password",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "avatar",
            "fit_profile",
            "fit_profile_updated_at",
            "is_active",
            "account_deleted_at",
            "marketing_opt_in_at",
            "marketing_opt_in_version",
        ]
    )

    return {
        "status": "deleted",
        "deleted_at": locked_user.account_deleted_at.isoformat(),
        "retained_order_count": locked_user.orders.count(),
        "retained_payment_count": Payment.objects.filter(user=locked_user).count(),
        "deleted_email": original_email,
    }
