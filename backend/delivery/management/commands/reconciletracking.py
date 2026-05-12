from django.core.management.base import BaseCommand

from delivery.models import OrderDeliverySnapshot
from delivery.services import refresh_order_tracking_from_provider


class Command(BaseCommand):
    help = "Refresh provider tracking state for active shipment snapshots."

    TERMINAL_TRACKING_STATUSES = {
        OrderDeliverySnapshot.TrackingStatus.DELIVERED,
        OrderDeliverySnapshot.TrackingStatus.RETURNED,
    }

    def add_arguments(self, parser):
        parser.add_argument("--order-id", type=int)
        parser.add_argument("--provider-code")
        parser.add_argument("--limit", type=int, default=50)

    def handle(self, *args, **options):
        queryset = (
            OrderDeliverySnapshot.objects.select_related("order")
            .exclude(external_shipment_id="")
            .exclude(tracking_status__in=self.TERMINAL_TRACKING_STATUSES)
            .order_by("created_at", "order_id")
        )

        if options["order_id"]:
            queryset = queryset.filter(order_id=options["order_id"])
        if options["provider_code"]:
            queryset = queryset.filter(provider_code=options["provider_code"])

        snapshots = list(queryset[: options["limit"]])
        counts = {
            "checked": 0,
            "updated": 0,
            "unchanged": 0,
            "failed": 0,
        }

        for snapshot in snapshots:
            counts["checked"] += 1
            try:
                result = refresh_order_tracking_from_provider(order=snapshot.order)
            except Exception as exc:
                counts["failed"] += 1
                self.stderr.write(
                    self.style.ERROR(
                        "order "
                        f"#{snapshot.order_id}: tracking reconciliation failed ({exc})"
                    )
                )
                continue

            if result["updated"]:
                counts["updated"] += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        "order "
                        f"#{snapshot.order_id}: tracking updated -> "
                        f"{result['snapshot'].tracking_status}"
                    )
                )
                continue

            counts["unchanged"] += 1
            self.stdout.write(
                self.style.WARNING(
                    f"order #{snapshot.order_id}: provider returned no new tracking event"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Tracking reconciliation summary: "
                f"checked={counts['checked']} "
                f"updated={counts['updated']} "
                f"unchanged={counts['unchanged']} "
                f"failed={counts['failed']}"
            )
        )
