from __future__ import annotations

from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

from users.staff_roles import sync_staff_role_groups


@dataclass(frozen=True)
class DemoUserSpec:
    username: str
    email: str
    password: str
    is_superuser: bool = False
    is_staff: bool = False
    groups: tuple[str, ...] = ()


DEMO_USERS: tuple[DemoUserSpec, ...] = (
    DemoUserSpec(
        username="admin",
        email="admin@example.com",
        password="12345678",
        is_superuser=True,
        is_staff=True,
    ),
    DemoUserSpec(
        username="owner",
        email="owner@example.com",
        password="12345678",
        is_staff=True,
        groups=("owner",),
    ),
    DemoUserSpec(
        username="catalog",
        email="catalog@example.com",
        password="12345678",
        is_staff=True,
        groups=("catalog_manager",),
    ),
    DemoUserSpec(
        username="orders",
        email="orders@example.com",
        password="12345678",
        is_staff=True,
        groups=("order_manager",),
    ),
    DemoUserSpec(
        username="inventory",
        email="inventory@example.com",
        password="12345678",
        is_staff=True,
        groups=("inventory_manager",),
    ),
    DemoUserSpec(
        username="warehouse",
        email="warehouse@example.com",
        password="12345678",
        is_staff=True,
        groups=("warehouse_operator",),
    ),
    DemoUserSpec(
        username="support",
        email="support@example.com",
        password="12345678",
        is_staff=True,
        groups=("support_agent",),
    ),
    DemoUserSpec(
        username="accountant",
        email="accountant@example.com",
        password="12345678",
        is_staff=True,
        groups=("accountant",),
    ),
    DemoUserSpec(
        username="shopper",
        email="shopper@example.com",
        password="12345678",
        is_staff=False,
    ),
)


class Command(BaseCommand):
    help = "Create demo users for local development (admin + staff roles + shopper)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force-passwords",
            action="store_true",
            help="Reset passwords for existing demo users.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force_passwords = bool(options["force_passwords"])
        sync_staff_role_groups()

        User = get_user_model()
        created = 0
        updated = 0

        for spec in DEMO_USERS:
            user, was_created = User.objects.get_or_create(
                username=spec.username,
                defaults={
                    "email": spec.email,
                    "is_staff": spec.is_staff or spec.is_superuser,
                    "is_superuser": spec.is_superuser,
                    "is_active": True,
                },
            )

            changed = False

            if user.email != spec.email:
                user.email = spec.email
                changed = True

            desired_is_staff = spec.is_staff or spec.is_superuser
            if bool(user.is_staff) != desired_is_staff:
                user.is_staff = desired_is_staff
                changed = True

            if bool(user.is_superuser) != bool(spec.is_superuser):
                user.is_superuser = spec.is_superuser
                changed = True

            if was_created or force_passwords:
                user.set_password(spec.password)
                changed = True

            if changed:
                user.save()

            user.groups.clear()
            for group_name in spec.groups:
                group, _ = Group.objects.get_or_create(name=group_name)
                user.groups.add(group)

            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo users ready. created={created} updated={updated} total={len(DEMO_USERS)}"
            )
        )
