from dataclasses import dataclass, field

from django.conf import settings
from rest_framework.exceptions import ValidationError

from delivery.models import OrderDeliverySnapshot


@dataclass(frozen=True)
class DeliveryTrackingFetchResult:
    tracking_status: str
    event_id: str
    external_shipment_id: str = ""
    location: str = ""
    message: str = ""
    payload: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ShipmentCreationResult:
    provider: str
    external_shipment_id: str
    track_number: str
    message: str = ""
    payload: dict = field(default_factory=dict)


class BaseDeliveryProviderAdapter:
    provider_code = ""

    def create_shipment(self, *, snapshot):
        raise NotImplementedError

    def fetch_tracking_status(self, *, snapshot):
        return None


class ManualDeliveryProviderAdapter(BaseDeliveryProviderAdapter):
    provider_code = "manual"

    def create_shipment(self, *, snapshot):
        shipment_id = snapshot.external_shipment_id or f"manual-shipment-{snapshot.order_id}"
        return ShipmentCreationResult(
            provider=self.provider_code,
            external_shipment_id=shipment_id,
            track_number=f"MANUAL-{snapshot.order_id}",
            message="Отправка подготовлена в локальном режиме. Внешний delivery provider ещё не подключён.",
            payload={"provider": self.provider_code, "mode": "local"},
        )


class CDEKSandboxDeliveryAdapter(BaseDeliveryProviderAdapter):
    provider_code = "cdek"

    STATUS_MAPPING = {
        "accepted": OrderDeliverySnapshot.TrackingStatus.HANDED_OVER,
        "in_transit": OrderDeliverySnapshot.TrackingStatus.IN_TRANSIT,
        "on_way": OrderDeliverySnapshot.TrackingStatus.IN_TRANSIT,
        "ready_for_pickup": OrderDeliverySnapshot.TrackingStatus.IN_TRANSIT,
        "courier": OrderDeliverySnapshot.TrackingStatus.OUT_FOR_DELIVERY,
        "delivered": OrderDeliverySnapshot.TrackingStatus.DELIVERED,
        "failed": OrderDeliverySnapshot.TrackingStatus.FAILED,
        "not_delivered": OrderDeliverySnapshot.TrackingStatus.FAILED,
        "returned": OrderDeliverySnapshot.TrackingStatus.RETURNED,
        "returning": OrderDeliverySnapshot.TrackingStatus.RETURNED,
    }

    def create_shipment(self, *, snapshot):
        shipment_id = snapshot.external_shipment_id or f"cdek-sandbox-{snapshot.order_id}"
        return ShipmentCreationResult(
            provider=self.provider_code,
            external_shipment_id=shipment_id,
            track_number=f"CDEK-{snapshot.order_id}",
            message="CDEK sandbox-отправка подготовлена.",
            payload={
                "provider": self.provider_code,
                "mode": "sandbox",
                "shipment_id": shipment_id,
            },
        )

    def fetch_tracking_status(self, *, snapshot):
        effective_external_id = snapshot.external_shipment_id
        if not effective_external_id:
            return None

        provider_statuses = getattr(
            settings, "DELIVERY_PROVIDER_TRACKING_OVERRIDES", {}
        )
        provider_overrides = provider_statuses.get(self.provider_code, {})
        raw_override = provider_overrides.get(effective_external_id)
        if not raw_override:
            return None

        if isinstance(raw_override, str):
            raw_status = raw_override
            location = ""
            message = ""
            payload = {"raw_status": raw_status}
        elif isinstance(raw_override, dict):
            raw_status = str(raw_override.get("status", "")).strip()
            location = str(raw_override.get("location", "")).strip()
            message = str(raw_override.get("message", "")).strip()
            payload = dict(raw_override)
        else:
            raise ValidationError(
                {
                    "delivery": {
                        "code": "provider_tracking_override_invalid",
                        "message": "Sandbox-ответ доставки имеет неподдерживаемый формат.",
                    }
                }
            )

        normalized_status = self.STATUS_MAPPING.get(raw_status.lower())
        if not normalized_status:
            raise ValidationError(
                {
                    "delivery": {
                        "code": "provider_tracking_status_unsupported",
                        "message": "Sandbox-статус доставки не поддерживается.",
                    }
                }
            )

        return DeliveryTrackingFetchResult(
            tracking_status=normalized_status,
            event_id=f"tracking-refresh:{effective_external_id}:{normalized_status}",
            external_shipment_id=effective_external_id,
            location=location,
            message=message or "Статус доставки синхронизирован из sandbox-ответа.",
            payload={
                "provider": self.provider_code,
                "status_source": "sandbox_override",
                "raw_status": raw_status,
                **payload,
            },
        )


_MANUAL = ManualDeliveryProviderAdapter()
_PROVIDERS = {
    "manual": _MANUAL,
    "local": _MANUAL,
    "cdek": CDEKSandboxDeliveryAdapter(),
}


def get_delivery_provider(provider_code):
    return _PROVIDERS.get(provider_code)


def fetch_provider_delivery_tracking_status(*, provider_code, snapshot):
    provider = get_delivery_provider(provider_code)
    if provider is None:
        return None
    return provider.fetch_tracking_status(snapshot=snapshot)
