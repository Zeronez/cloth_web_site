from django.core.management.base import BaseCommand

from payments.models import Payment
from payments.services import fetch_provider_payment_status, process_payment_webhook


class Command(BaseCommand):
    help = "Reconcile non-terminal payments against provider status fetch adapters."

    def add_arguments(self, parser):
        parser.add_argument("--payment-id", type=int)
        parser.add_argument("--order-id", type=int)
        parser.add_argument("--provider-code")
        parser.add_argument("--limit", type=int, default=50)
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Inspect reconciliation candidates without mutating payment state.",
        )

    def handle(self, *args, **options):
        queryset = (
            Payment.objects.select_related("order", "method", "user")
            .exclude(status__in=Payment.TERMINAL_STATUSES)
            .order_by("created_at", "id")
        )

        if options["payment_id"]:
            queryset = queryset.filter(pk=options["payment_id"])
        if options["order_id"]:
            queryset = queryset.filter(order_id=options["order_id"])
        if options["provider_code"]:
            queryset = queryset.filter(provider_code=options["provider_code"])

        payments = list(queryset[: options["limit"]])
        counts = {
            "checked": 0,
            "processed": 0,
            "replayed": 0,
            "unchanged": 0,
            "no_update": 0,
            "failed": 0,
        }

        for payment in payments:
            counts["checked"] += 1
            try:
                fetch_result = fetch_provider_payment_status(
                    provider_code=payment.provider_code,
                    payment=payment,
                    external_payment_id=payment.external_payment_id,
                )
                if fetch_result is None:
                    counts["no_update"] += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"payment #{payment.id}: provider returned no update"
                        )
                    )
                    continue

                if options["dry_run"]:
                    counts["processed"] += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            "payment "
                            f"#{payment.id}: dry-run would apply {fetch_result.status} "
                            f"via {fetch_result.event_id}"
                        )
                    )
                    continue

                result = process_payment_webhook(
                    provider_code=payment.provider_code,
                    event_id=fetch_result.event_id,
                    status=fetch_result.status,
                    order_id=payment.order_id,
                    payment_id=payment.id,
                    external_payment_id=(
                        fetch_result.external_payment_id or payment.external_payment_id
                    ),
                    payload=fetch_result.payload,
                )
            except Exception as exc:
                counts["failed"] += 1
                self.stderr.write(
                    self.style.ERROR(
                        f"payment #{payment.id}: reconciliation failed ({exc})"
                    )
                )
                continue

            if result["code"] == "processed":
                counts["processed"] += 1
            elif result["code"] == "event_replayed":
                counts["replayed"] += 1
            else:
                counts["unchanged"] += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"payment #{payment.id}: {result['code']} -> {result['payment'].status}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Payment reconciliation summary: "
                f"checked={counts['checked']} "
                f"processed={counts['processed']} "
                f"replayed={counts['replayed']} "
                f"unchanged={counts['unchanged']} "
                f"no_update={counts['no_update']} "
                f"failed={counts['failed']}"
            )
        )
