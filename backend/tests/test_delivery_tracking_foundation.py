from decimal import Decimal

import pytest

from delivery.models import DeliveryTrackingEvent, OrderDeliverySnapshot
from delivery.services import (
    create_shipment_for_order,
    ensure_shipment_for_paid_order,
    refresh_order_tracking_from_provider,
    sync_order_tracking_status,
)
from orders.models import Order


pytestmark = pytest.mark.django_db


def shipping_payload(**overrides):
    payload = {
        "shipping_name": "QA Shopper",
        "shipping_phone": "+15551234567",
        "shipping_country": "RU",
        "shipping_city": "Moscow",
        "shipping_postal_code": "101000",
        "shipping_line1": "Test street 1",
        "shipping_line2": "",
    }
    payload.update(overrides)
    return payload


def create_delivery_method():
    from delivery.models import DeliveryMethod

    return DeliveryMethod.objects.create(
        code="courier-msk",
        name="Курьер по Москве",
        kind=DeliveryMethod.Kind.COURIER,
        price_amount=Decimal("350.00"),
    )


def create_order_with_snapshot(user, status=Order.Status.PAID, provider_code="manual"):
    from delivery.services import create_order_delivery_snapshot

    order = Order.objects.create(
        user=user,
        total_amount=Decimal("125.00"),
        status=status,
        **shipping_payload(),
    )
    snapshot = create_order_delivery_snapshot(
        order, create_delivery_method(), shipping_payload()
    )
    snapshot.provider_code = provider_code
    snapshot.save(update_fields=["provider_code"])
    return order


def test_create_shipment_registers_shipment_and_sets_tracking_number(user):
    order = create_order_with_snapshot(user, status=Order.Status.PAID)

    snapshot = create_shipment_for_order(
        order=order,
        provider_code="cdek",
        external_shipment_id="SHIP-1001",
        track_number="TRACK-1001",
    )

    order.refresh_from_db()
    assert order.status == Order.Status.PAID
    assert order.track_number == "TRACK-1001"
    assert snapshot.provider_code == "cdek"
    assert snapshot.tracking_status == OrderDeliverySnapshot.TrackingStatus.CREATED
    assert DeliveryTrackingEvent.objects.filter(
        snapshot=snapshot,
        event_type="shipment_created",
    ).exists()


def test_ensure_shipment_for_paid_order_is_idempotent(user):
    order = create_order_with_snapshot(user, status=Order.Status.PAID)

    first_snapshot, first_created = ensure_shipment_for_paid_order(order=order)
    second_snapshot, second_created = ensure_shipment_for_paid_order(order=order)

    assert first_created is True
    assert second_created is False
    assert first_snapshot.id == second_snapshot.id
    assert first_snapshot.external_shipment_id == f"manual-shipment-{order.id}"


def test_ensure_shipment_uses_provider_shaped_contract(user):
    order = create_order_with_snapshot(
        user, status=Order.Status.PAID, provider_code="cdek"
    )

    snapshot, created = ensure_shipment_for_paid_order(order=order)

    order.refresh_from_db()
    assert created is True
    assert snapshot.provider_code == "cdek"
    assert snapshot.tracking_status == OrderDeliverySnapshot.TrackingStatus.CREATED
    assert snapshot.external_shipment_id == f"cdek-sandbox-{order.id}"
    assert order.track_number == f"CDEK-{order.id}"


def test_tracking_sync_to_delivered_updates_order_and_snapshot(user):
    order = create_order_with_snapshot(user, status=Order.Status.PAID)
    create_shipment_for_order(
        order=order,
        provider_code="cdek",
        external_shipment_id="SHIP-1002",
        track_number="TRACK-1002",
    )

    event, created = sync_order_tracking_status(
        order=order,
        tracking_status=OrderDeliverySnapshot.TrackingStatus.DELIVERED,
        external_event_id="track-event-1",
        location="Москва, пункт выдачи",
        message="Получено получателем.",
        provider_code="cdek",
    )

    order.refresh_from_db()
    snapshot = order.delivery_snapshot
    assert created is True
    assert event.new_status == OrderDeliverySnapshot.TrackingStatus.DELIVERED
    assert snapshot.tracking_status == OrderDeliverySnapshot.TrackingStatus.DELIVERED
    assert snapshot.current_location == "Москва, пункт выдачи"
    assert order.status == Order.Status.DELIVERED


def test_tracking_sync_is_idempotent_by_external_event_id(user):
    order = create_order_with_snapshot(user, status=Order.Status.PAID)
    create_shipment_for_order(
        order=order,
        provider_code="cdek",
        external_shipment_id="SHIP-1003",
        track_number="TRACK-1003",
    )

    first_event, first_created = sync_order_tracking_status(
        order=order,
        tracking_status=OrderDeliverySnapshot.TrackingStatus.IN_TRANSIT,
        external_event_id="track-event-duplicate",
        location="Сортировочный центр",
        provider_code="cdek",
    )
    second_event, second_created = sync_order_tracking_status(
        order=order,
        tracking_status=OrderDeliverySnapshot.TrackingStatus.IN_TRANSIT,
        external_event_id="track-event-duplicate",
        location="Сортировочный центр",
        provider_code="cdek",
    )

    assert first_created is True
    assert second_created is False
    assert first_event.id == second_event.id
    assert (
        DeliveryTrackingEvent.objects.filter(
            snapshot=order.delivery_snapshot,
            external_event_id="track-event-duplicate",
        ).count()
        == 1
    )


def test_order_detail_returns_tracking_status_and_events(authenticated_client, user):
    order = create_order_with_snapshot(user, status=Order.Status.PAID)
    create_shipment_for_order(
        order=order,
        provider_code="cdek",
        external_shipment_id="SHIP-1004",
        track_number="TRACK-1004",
    )
    sync_order_tracking_status(
        order=order,
        tracking_status=OrderDeliverySnapshot.TrackingStatus.OUT_FOR_DELIVERY,
        external_event_id="track-event-2",
        location="Москва",
        message="Курьер выехал.",
        provider_code="cdek",
    )

    response = authenticated_client.get(f"/api/orders/{order.id}/")

    assert response.status_code == 200
    assert response.data["track_number"] == "TRACK-1004"
    assert response.data["delivery"]["tracking_status"] == "out_for_delivery"
    assert response.data["delivery"]["tracking_status_label"] == "Курьер уже едет"
    assert response.data["delivery"]["provider_code"] == "cdek"
    assert response.data["delivery"]["tracking_events"][-1]["location"] == "Москва"


def test_provider_tracking_refresh_updates_order_from_sandbox_override(user, settings):
    order = create_order_with_snapshot(user, status=Order.Status.PAID)
    create_shipment_for_order(
        order=order,
        provider_code="cdek",
        external_shipment_id="SHIP-1005",
        track_number="TRACK-1005",
    )
    settings.DELIVERY_PROVIDER_TRACKING_OVERRIDES = {
        "cdek": {
            "SHIP-1005": {
                "status": "delivered",
                "location": "Москва, вручено",
                "message": "Заказ доставлен получателю.",
            }
        }
    }

    result = refresh_order_tracking_from_provider(order=order)

    order.refresh_from_db()
    snapshot = order.delivery_snapshot
    assert result["updated"] is True
    assert snapshot.tracking_status == OrderDeliverySnapshot.TrackingStatus.DELIVERED
    assert snapshot.current_location == "Москва, вручено"
    assert order.status == Order.Status.DELIVERED


def test_tracking_refresh_endpoint_returns_updated_order(
    authenticated_client, user, settings
):
    order = create_order_with_snapshot(user, status=Order.Status.PAID)
    create_shipment_for_order(
        order=order,
        provider_code="cdek",
        external_shipment_id="SHIP-1006",
        track_number="TRACK-1006",
    )
    settings.DELIVERY_PROVIDER_TRACKING_OVERRIDES = {
        "cdek": {
            "SHIP-1006": {
                "status": "courier",
                "location": "Москва",
                "message": "Курьер везёт заказ.",
            }
        }
    }

    response = authenticated_client.post(f"/api/orders/{order.id}/tracking-refresh/")

    assert response.status_code == 200
    assert response.data["track_number"] == "TRACK-1006"
    assert response.data["delivery"]["tracking_status"] == "out_for_delivery"
    assert response.data["delivery"]["current_location"] == "Москва"
