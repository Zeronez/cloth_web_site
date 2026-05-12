from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from audit.migration_safety import (
    collect_migration_safety_violations,
    format_violations,
)


class Command(BaseCommand):
    help = "Block destructive Django migrations unless they declare a backfill/deploy/rollback plan."

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR)
        violations = collect_migration_safety_violations(base_dir)
        if violations:
            raise CommandError(
                "Migration safety policy violations found:\n"
                f"{format_violations(violations)}"
            )

        self.stdout.write(self.style.SUCCESS("Migration safety policy check passed."))
