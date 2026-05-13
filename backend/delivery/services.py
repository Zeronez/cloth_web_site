from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError

from delivery.models import DeliveryMethod, DeliveryTrackingEvent, OrderDeliverySnapshot
from delivery.providers import (
    fetch_provider_delivery_tracking_status,
    get_delivery_provider,
)
from orders.models import Order


class DeliveryProviderUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "delivery_provider_temporarily_unavailable"
    default_detail = {
        "delivery": {
            "code": "delivery_provider_temporarily_unavailable",
            "message": "Служба расчёта доставки временно недоступна. Попробуйте ещё раз чуть позже.",
        }
    }


def _delivery_provider_error(code, message):
    return {"delivery": {"code": code, "message": message}}


def _delivery_fixture_key(*, country="", city="", postal_code=""):
    return "|".join(
        [
            str(country or "").strip().upper(),
            str(city or "").strip().lower(),
            str(postal_code or "").strip(),
        ]
    )


def _delivery_fixture_quote(*, country="", city="", postal_code=""):
    key = _delivery_fixture_key(
        country=country,
        city=city,
        postal_code=postal_code,
    )
    overrides = getattr(settings, "DELIVERY_METHOD_AVAILABILITY_OVERRIDES", {})
    fixture = overrides.get(key, {})
    if not isinstance(fixture, dict):
        return {}
    error = fixture.get("error")
    if isinstance(error, dict):
        raise DeliveryProviderUnavailable(
            _delivery_provider_error(
                str(error.get("code", "")).strip()
                or "delivery_provider_temporarily_unavailable",
                str(error.get("message", "")).strip()
                or "Служба расчёта доставки временно недоступна. Попробуйте ещё раз чуть позже.",
            )
        )
    if isinstance(error, str) and error.strip():
        raise DeliveryProviderUnavailable(
            _delivery_provider_error(
                "delivery_provider_temporarily_unavailable",
                error.strip(),
            )
        )
    return fixture


def _pickup_point_fixture(*, method_code, country="", city="", postal_code=""):
    key = _delivery_fixture_key(
        country=country,
        city=city,
        postal_code=postal_code,
    )
    overrides = getattr(settings, "DELIVERY_PICKUP_POINT_OVERRIDES", {})
    fixture = overrides.get(key, {})
    if not isinstance(fixture, dict):
        return []
    points = fixture.get(str(method_code), [])
    if not isinstance(points, list):
        return []
    return points


def _quoted_delivery_price(method, *, country="", city="", postal_code=""):
    if method is None:
        return Decimal("0.00")
    fixture = _delivery_fixture_quote(
        country=country,
        city=city,
        postal_code=postal_code,
    )
    price_overrides = fixture.get("price_overrides", {})
    if not isinstance(price_overrides, dict):
        price_overrides = {}
    raw_price = price_overrides.get(method.code)
    if raw_price in {None, ""}:
        return method.price_amount
    return Decimal(str(raw_price))


def get_available_delivery_methods(*, country="", city="", postal_code=""):
    methods = list(
        DeliveryMethod.objects.filter(is_active=True).order_by("sort_order", "name")
    )
    fixture = _delivery_fixture_quote(
        country=country,
        city=city,
        postal_code=postal_code,
    )
    available_codes = fixture.get("available_methods")
    if isinstance(available_codes, list):
        allowed = set(str(code) for code in available_codes)
        methods = [method for method in methods if method.code in allowed]

    for method in methods:
        method.quoted_price_amount = _quoted_delivery_price(
            method,
            country=country,
            city=city,
            postal_code=postal_code,
        )
    return methods


def resolve_delivery_method(code=None, *, country="", city="", postal_code=""):
    methods = get_available_delivery_methods(
        country=country,
        city=city,
        postal_code=postal_code,
    )
    if code:
        try:
            return next(method for method in methods if method.code == code)
        except StopIteration as exc:
            raise ValidationError(
                {
                    "delivery_method_code": {
                        "code": "delivery_method_unavailable",
                        "message": "Delivery method is not available.",
                    }
                }
            ) from exc
    return methods[0] if methods else None


def delivery_price_for(method, *, country="", city="", postal_code=""):
    return _quoted_delivery_price(
        method,
        country=country,
        city=city,
        postal_code=postal_code,
    )


def search_pickup_points(
    *,
    method_code,
    country="",
    city="",
    postal_code="",
    query="",
):
    method = resolve_delivery_method(
        method_code,
        country=country,
        city=city,
        postal_code=postal_code,
    )
    if method is None or method.kind != DeliveryMethod.Kind.PICKUP:
        raise ValidationError(
            {
                "delivery_method_code": {
                    "code": "pickup_method_required",
                    "message": "Pickup points are available only for pickup delivery methods.",
                }
            }
        )

    points = _pickup_point_fixture(
        method_code=method.code,
        country=country,
        city=city,
        postal_code=postal_code,
    )
    normalized_query = str(query or "").strip().lower()
    if normalized_query:
        points = [
            point
            for point in points
            if normalized_query in str(point.get("name", "")).lower()
            or normalized_query in str(point.get("address", "")).lower()
            or normalized_query in str(point.get("code", "")).lower()
        ]
    return points


def create_order_delivery_snapshot(order, method, shipping_data):
    if method is None:
        return None
    quoted_price_amount = delivery_price_for(
        method,
        country=shipping_data.get("shipping_country", ""),
        city=shipping_data.get("shipping_city", ""),
        postal_code=shipping_data.get("shipping_postal_code", ""),
    )
    return OrderDeliverySnapshot.objects.create(
        order=order,
        delivery_method=method,
        method_code=method.code,
        method_name=method.name,
        method_kind=method.kind,
        price_amount=quoted_price_amount,
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
    from orders.services import transition_order_status

    if tracking_status == OrderDeliverySnapshot.TrackingStatus.CREATED:
        return

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
            order, _changed, _old_status, _was_restocked = transition_order_status(
                order=order,
                new_status=Order.Status.SHIPPED,
            )
        return

    if tracking_status == OrderDeliverySnapshot.TrackingStatus.DELIVERED:
        if order.status in {
            Order.Status.PAID,
            Order.Status.PICKING,
            Order.Status.PACKED,
        }:
            order, _changed, _old_status, _was_restocked = transition_order_status(
                order=order,
                new_status=Order.Status.SHIPPED,
            )
        if order.status != Order.Status.DELIVERED and order.can_transition_to(
            Order.Status.DELIVERED
        ):
            order, _changed, _old_status, _was_restocked = transition_order_status(
                order=order,
                new_status=Order.Status.DELIVERED,
            )
        return

    if tracking_status == OrderDeliverySnapshot.TrackingStatus.RETURNED:
        if order.status != Order.Status.RETURNED and order.can_transition_to(
            Order.Status.RETURNED
        ):
            order, _changed, _old_status, _was_restocked = transition_order_status(
                order=order,
                new_status=Order.Status.RETURNED,
            )


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
    snapshot.tracking_status = OrderDeliverySnapshot.TrackingStatus.CREATED
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
        message=message or "Оформлена накладная и создано отправление.",
        payload=payload or {},
        location=snapshot.city,
        happened_at=timezone.now(),
    )
    snapshot.refresh_from_db()
    return snapshot


@transaction.atomic
def ensure_shipment_for_paid_order(*, order):
    snapshot = (
        OrderDeliverySnapshot.objects.select_for_update()
        .select_related("order")
        .filter(order=order)
        .first()
    )
    if snapshot is None:
        raise ValidationError(
            {
                "delivery": {
                    "code": "delivery_snapshot_not_found",
                    "message": "Для заказа ещё не создан delivery snapshot.",
                }
            }
        )
    if snapshot.external_shipment_id:
        return snapshot, False

    provider = get_delivery_provider(snapshot.provider_code)
    if provider is None:
        raise ValidationError(
            {
                "delivery": {
                    "code": "delivery_provider_not_configured",
                    "message": "Провайдер доставки не настроен.",
                }
            }
        )

    shipment = provider.create_shipment(snapshot=snapshot)
    created_snapshot = create_shipment_for_order(
        order=order,
        provider_code=shipment.provider,
        external_shipment_id=shipment.external_shipment_id,
        track_number=shipment.track_number,
        message=shipment.message,
        payload=shipment.payload,
    )
    return created_snapshot, True


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


@transaction.atomic
def refresh_order_tracking_from_provider(*, order):
    snapshot = (
        OrderDeliverySnapshot.objects.select_for_update()
        .select_related("order")
        .filter(order=order)
        .first()
    )
    if snapshot is None:
        raise ValidationError(
            {
                "delivery": {
                    "code": "delivery_snapshot_not_found",
                    "message": "Для заказа ещё не создан delivery snapshot.",
                }
            }
        )

    fetch_result = fetch_provider_delivery_tracking_status(
        provider_code=snapshot.provider_code,
        snapshot=snapshot,
    )
    if fetch_result is None:
        return {
            "snapshot": snapshot,
            "updated": False,
            "message": "Новых событий доставки у провайдера пока нет.",
        }

    event, created = sync_order_tracking_status(
        order=order,
        tracking_status=fetch_result.tracking_status,
        external_event_id=fetch_result.event_id,
        external_shipment_id=fetch_result.external_shipment_id,
        location=fetch_result.location,
        message=fetch_result.message,
        provider_code=snapshot.provider_code,
        payload=fetch_result.payload,
    )
    snapshot.refresh_from_db()
    order.refresh_from_db()
    return {
        "snapshot": snapshot,
        "event": event,
        "updated": created,
        "message": (
            "Статус доставки синхронизирован."
            if created
            else "Событие доставки уже было обработано ранее."
        ),
    }
