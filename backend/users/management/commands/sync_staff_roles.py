from django.core.management.base import BaseCommand

from users.staff_roles import STAFF_ROLE_GROUPS, sync_staff_role_groups


class Command(BaseCommand):
    help = "Create or update AnimeAttire staff role groups and their permissions."

    def handle(self, *args, **options):
        groups = sync_staff_role_groups()
        self.stdout.write(
            self.style.SUCCESS(
                "Synced staff roles: " + ", ".join(group.name for group in groups)
            )
        )
        self.stdout.write(
            f"Total staff role groups configured: {len(STAFF_ROLE_GROUPS)}"
        )
