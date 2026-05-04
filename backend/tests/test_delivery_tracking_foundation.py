from decimal import Decimal

import pytest

from delivery.models import DeliveryTrackingEvent, OrderDeliverySnapshot
from delivery.services import create_shipment_for_order, sync_order_tracking_status
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


def create_order_with_snapshot(user, status=Order.Status.PAID):
    from delivery.services import create_order_delivery_snapshot

    order = Order.objects.create(
        user=user,
        total_amount=Decimal("125.00"),
        status=status,
        **shipping_payload(),
    )
    create_order_delivery_snapshot(order, create_delivery_method(), shipping_payload())
    return order


def test_create_shipment_marks_order_shipped_and_sets_tracking_number(user):
    order = create_order_with_snapshot(user, status=Order.Status.PAID)

    snapshot = create_shipment_for_order(
        order=order,
        provider_code="cdek",
        external_shipment_id="SHIP-1001",
        track_number="TRACK-1001",
    )

    order.refresh_from_db()
    assert order.status == Order.Status.SHIPPED
    assert order.track_number == "TRACK-1001"
    assert snapshot.provider_code == "cdek"
    assert snapshot.tracking_status == OrderDeliverySnapshot.TrackingStatus.HANDED_OVER
    assert DeliveryTrackingEvent.objects.filter(
        snapshot=snapshot,
        event_type="shipment_created",
    ).exists()


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
