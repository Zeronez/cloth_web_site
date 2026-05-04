from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from delivery.models import DeliveryMethod, DeliveryTrackingEvent, OrderDeliverySnapshot
from orders.models import Order


def get_available_delivery_methods():
    return DeliveryMethod.objects.filter(is_active=True).order_by("sort_order", "name")


def resolve_delivery_method(code=None):
    methods = get_available_delivery_methods()
    if code:
        try:
            return methods.get(code=code)
        except DeliveryMethod.DoesNotExist as exc:
            raise ValidationError(
                {
                    "delivery_method_code": {
                        "code": "delivery_method_unavailable",
                        "message": "Способ доставки недоступен.",
                    }
                }
            ) from exc
    return methods.first()


def delivery_price_for(method):
    if method is None:
        return Decimal("0.00")
    return method.price_amount


def create_order_delivery_snapshot(order, method, shipping_data):
    if method is None:
        return None
    return OrderDeliverySnapshot.objects.create(
        order=order,
        delivery_method=method,
        method_code=method.code,
        method_name=method.name,
        method_kind=method.kind,
        price_amount=method.price_amount,
        currency=method.currency,
        estimated_days_min=method.estimated_days_min,
        estimated_days_max=method.estimated_days_max,
        provider_code="manual",
        tracking_status=OrderDeliverySnapshot.TrackingStatus.PENDING,
        recipient_name=shipping_data["shipping_name"],
        recipient_phone=shipping_data["shipping_phone"],
        country=shipping_data["shipping_country"],
        city=shipping_data["shipping_city"],
        postal_code=shipping_data["shipping_postal_code"],
        line1=shipping_data["shipping_line1"],
        line2=shipping_data.get("shipping_line2", ""),
    )


def _sync_order_with_tracking_status(order, tracking_status):
    if tracking_status in {
        OrderDeliverySnapshot.TrackingStatus.HANDED_OVER,
        OrderDeliverySnapshot.TrackingStatus.IN_TRANSIT,
        OrderDeliverySnapshot.TrackingStatus.OUT_FOR_DELIVERY,
    }:
        if order.status in {
            Order.Status.PAID,
            Order.Status.PICKING,
            Order.Status.PACKED,
        }:
            order.transition_to(Order.Status.SHIPPED)
        return

    if tracking_status == OrderDeliverySnapshot.TrackingStatus.DELIVERED:
        if order.status != Order.Status.DELIVERED and order.can_transition_to(
            Order.Status.DELIVERED
        ):
            order.transition_to(Order.Status.DELIVERED)
        return

    if tracking_status == OrderDeliverySnapshot.TrackingStatus.RETURNED:
        if order.status != Order.Status.RETURNED and order.can_transition_to(
            Order.Status.RETURNED
        ):
            order.transition_to(Order.Status.RETURNED)


@transaction.atomic
def create_shipment_for_order(
    *,
    order,
    provider_code="manual",
    external_shipment_id="",
    track_number="",
    message="",
    payload=None,
):
    snapshot = (
        OrderDeliverySnapshot.objects.select_for_update()
        .select_related("order")
        .get(order=order)
    )
    previous_status = snapshot.tracking_status
    snapshot.provider_code = provider_code or snapshot.provider_code
    if external_shipment_id:
        snapshot.external_shipment_id = external_shipment_id
    snapshot.tracking_status = OrderDeliverySnapshot.TrackingStatus.HANDED_OVER
    snapshot.last_tracking_sync_at = timezone.now()
    snapshot.save(
        update_fields=[
            "provider_code",
            "external_shipment_id",
            "tracking_status",
            "last_tracking_sync_at",
        ]
    )
    if track_number and order.track_number != track_number:
        order.track_number = track_number
        order.save(update_fields=["track_number", "updated_at"])
    _sync_order_with_tracking_status(order, snapshot.tracking_status)
    DeliveryTrackingEvent.objects.create(
        snapshot=snapshot,
        event_type="shipment_created",
        previous_status=previous_status,
        new_status=snapshot.tracking_status,
        message=message or "Заказ передан в доставку.",
        payload=payload or {},
        location=snapshot.city,
        happened_at=timezone.now(),
    )
    snapshot.refresh_from_db()
    return snapshot


@transaction.atomic
def sync_order_tracking_status(
    *,
    order,
    tracking_status,
    external_event_id="",
    external_shipment_id="",
    location="",
    message="",
    provider_code="",
    payload=None,
    happened_at=None,
):
    snapshot = (
        OrderDeliverySnapshot.objects.select_for_update()
        .select_related("order")
        .get(order=order)
    )
    if external_event_id:
        existing_event = DeliveryTrackingEvent.objects.filter(
            snapshot=snapshot,
            external_event_id=external_event_id,
        ).first()
        if existing_event is not None:
            return existing_event, False

    previous_status = snapshot.tracking_status
    update_fields = ["tracking_status", "last_tracking_sync_at"]
    snapshot.tracking_status = tracking_status
    snapshot.last_tracking_sync_at = happened_at or timezone.now()
    if external_shipment_id:
        snapshot.external_shipment_id = external_shipment_id
        update_fields.append("external_shipment_id")
    if provider_code:
        snapshot.provider_code = provider_code
        update_fields.append("provider_code")
    if location:
        snapshot.current_location = location
        update_fields.append("current_location")
    snapshot.save(update_fields=update_fields)

    _sync_order_with_tracking_status(order, tracking_status)
    event = DeliveryTrackingEvent.objects.create(
        snapshot=snapshot,
        event_type="tracking_sync",
        previous_status=previous_status,
        new_status=tracking_status,
        message=message,
        location=location,
        payload=payload or {},
        external_event_id=external_event_id,
        happened_at=happened_at,
    )
    snapshot.refresh_from_db()
    return event, True
