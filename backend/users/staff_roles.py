from django.contrib.auth.models import Group, Permission


ROLE_OWNER = "owner"
ROLE_CATALOG_MANAGER = "catalog_manager"
ROLE_ORDER_MANAGER = "order_manager"
ROLE_WAREHOUSE_OPERATOR = "warehouse_operator"
ROLE_SUPPORT_AGENT = "support_agent"
ROLE_ACCOUNTANT = "accountant"

STAFF_ROLE_GROUPS = (
    ROLE_OWNER,
    ROLE_CATALOG_MANAGER,
    ROLE_ORDER_MANAGER,
    ROLE_WAREHOUSE_OPERATOR,
    ROLE_SUPPORT_AGENT,
    ROLE_ACCOUNTANT,
)

ROLE_PERMISSION_MAP = {
    ROLE_CATALOG_MANAGER: {
        "catalog.add_animefranchise",
        "catalog.change_animefranchise",
        "catalog.view_animefranchise",
        "catalog.add_category",
        "catalog.change_category",
        "catalog.view_category",
        "catalog.add_product",
        "catalog.change_product",
        "catalog.view_product",
        "catalog.add_productimage",
        "catalog.change_productimage",
        "catalog.view_productimage",
        "catalog.add_productvariant",
        "catalog.change_productvariant",
        "catalog.view_productvariant",
    },
    ROLE_ORDER_MANAGER: {
        "orders.change_order",
        "orders.view_order",
        "orders.view_orderitem",
        "delivery.change_deliverymethod",
        "delivery.view_deliverymethod",
        "delivery.change_orderdeliverysnapshot",
        "delivery.view_orderdeliverysnapshot",
        "delivery.view_deliverytrackingevent",
        "payments.view_payment",
        "payments.view_paymentevent",
        "payments.view_paymentmethod",
        "support.change_contactrequest",
        "support.view_contactrequest",
    },
    ROLE_WAREHOUSE_OPERATOR: {
        "orders.change_order",
        "orders.view_order",
        "orders.view_orderitem",
        "delivery.view_deliverymethod",
        "delivery.change_orderdeliverysnapshot",
        "delivery.view_orderdeliverysnapshot",
        "delivery.view_deliverytrackingevent",
    },
    ROLE_SUPPORT_AGENT: {
        "orders.change_order",
        "orders.view_order",
        "orders.view_orderitem",
        "delivery.view_orderdeliverysnapshot",
        "payments.view_payment",
        "payments.view_paymentevent",
        "support.change_contactrequest",
        "support.view_contactrequest",
    },
    ROLE_ACCOUNTANT: {
        "orders.view_order",
        "payments.view_payment",
        "payments.view_paymentevent",
        "payments.view_paymentmethod",
    },
}


def user_has_staff_role(user, *roles):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=roles).exists()


def sync_staff_role_groups():
    synced = []
    for group_name in STAFF_ROLE_GROUPS:
        group, _ = Group.objects.get_or_create(name=group_name)
        permission_codes = ROLE_PERMISSION_MAP.get(group_name, set())
        permissions = []
        for code in permission_codes:
            app_label, codename = code.split(".", 1)
            permissions.append(
                Permission.objects.get(
                    content_type__app_label=app_label,
                    codename=codename,
                )
            )
        group.permissions.set(permissions)
        synced.append(group)
    return synced
