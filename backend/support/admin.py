from django.contrib import admin

from support.models import ContactRequest


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "topic",
        "status",
        "name",
        "email",
        "order_number",
        "created_at",
    )
    list_filter = ("status", "topic", "created_at")
    search_fields = ("name", "email", "phone", "order_number", "message")
    readonly_fields = (
        "user",
        "name",
        "email",
        "phone",
        "topic",
        "order_number",
        "message",
        "user_agent",
        "ip_address",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            "Обращение",
            {
                "fields": (
                    "status",
                    "topic",
                    "name",
                    "email",
                    "phone",
                    "order_number",
                    "message",
                )
            },
        ),
        ("Клиент", {"fields": ("user", "ip_address", "user_agent")}),
        ("Внутренняя работа", {"fields": ("admin_notes",)}),
        ("Служебное", {"fields": ("created_at", "updated_at")}),
    )


# Register your models here.
