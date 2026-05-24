import pytest
from django.core.management import call_command

from catalog.models import AnimeFranchise, Category, Product, ProductVariant
from delivery.models import DeliveryMethod
from payments.models import PaymentMethod


pytestmark = pytest.mark.django_db


def test_seed_demo_store_creates_realistic_russian_demo_data_idempotently():
    call_command("seed_demo_store")
    first_counts = {
        "categories": Category.objects.count(),
        "franchises": AnimeFranchise.objects.count(),
        "products": Product.objects.count(),
        "variants": ProductVariant.objects.count(),
        "delivery_methods": DeliveryMethod.objects.count(),
        "payment_methods": PaymentMethod.objects.count(),
    }

    call_command("seed_demo_store")

    assert {
        "categories": Category.objects.count(),
        "franchises": AnimeFranchise.objects.count(),
        "products": Product.objects.count(),
        "variants": ProductVariant.objects.count(),
        "delivery_methods": DeliveryMethod.objects.count(),
        "payment_methods": PaymentMethod.objects.count(),
    } == first_counts
    assert first_counts == {
        "categories": 9,
        "franchises": 12,
        "products": 26,
        "variants": 78,
        "delivery_methods": 2,
        "payment_methods": 1,
    }

    assert Product.objects.filter(slug="neon-ronin-shell").exists() is False
    assert Product.objects.filter(slug="arcade-alley-hoodie").exists() is False
    assert Product.objects.filter(slug="ghost-frame-tee").exists() is False
    assert Product.objects.filter(slug="signal-cargo-pants").exists() is False

    new_product = Product.objects.get(slug="chainsaw-body")
    assert new_product.category.slug == "bodysuits"
    assert new_product.franchise.slug == "chainsaw-man"
    assert new_product.images.filter(is_approved=True).count() == 7

    assert DeliveryMethod.objects.filter(code="courier-cis", is_active=True).exists()
    payment_method = PaymentMethod.objects.get(code="manual-card")
    assert payment_method.provider_code == "placeholder"
    assert payment_method.session_mode == PaymentMethod.SessionMode.PLACEHOLDER
