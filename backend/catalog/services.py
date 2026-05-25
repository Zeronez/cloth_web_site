from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from catalog.models import Product, ProductImage, ProductVariant


SIZE_ORDER = {
    ProductVariant.Size.XS: 0,
    ProductVariant.Size.S: 1,
    ProductVariant.Size.M: 2,
    ProductVariant.Size.L: 3,
    ProductVariant.Size.XL: 4,
    ProductVariant.Size.XXL: 5,
    ProductVariant.Size.ONE_SIZE: 6,
}

STYLE_TOKENS = {
    "minimal": ("minimal", "clean", "basic", "essential"),
    "streetwear": ("streetwear", "oversized", "cargo", "jersey", "hoodie"),
    "dark_fantasy": ("dark", "fantasy", "gothic", "berserk", "chainsaw"),
    "sport": ("sport", "jersey", "track", "training"),
    "casual": ("casual", "daily", "everyday", "basic"),
}

DEFAULT_RECOMMENDATION = {
    "recommended_size": None,
    "confidence": "none",
    "risk_level": "high",
    "profile_ready": False,
    "missing_profile_fields": ["height_cm", "weight_kg", "preferred_fit"],
    "summary": "Заполните параметры фигуры, чтобы получить рекомендацию по размеру и образу.",
    "explanation": "Добавьте рост, вес и предпочтения по посадке в fit profile, чтобы включить умную примерочную.",
    "reasons": [],
    "risk_reasons": ["Недостаточно данных для персональной рекомендации."],
    "warnings": ["fit_profile_incomplete"],
    "fallback_action": "fill_fit_profile",
    "outfit": {"items": [], "total_price": None},
}


def _sorted_active_variants(product: Product) -> list[ProductVariant]:
    return sorted(
        (variant for variant in product.variants.all() if variant.is_active),
        key=lambda variant: (SIZE_ORDER.get(variant.size, 999), variant.id),
    )


def _nearest_available_size(
    target_size: str, available_sizes: Iterable[str]
) -> str | None:
    sizes = list(available_sizes)
    if not sizes:
        return None
    if target_size in sizes:
        return target_size
    target_rank = SIZE_ORDER.get(target_size, 999)
    return min(
        sizes,
        key=lambda size: (
            abs(SIZE_ORDER.get(size, 999) - target_rank),
            SIZE_ORDER.get(size, 999),
        ),
    )


def _shift_size(size: str | None, delta: int) -> str | None:
    if size is None or size == ProductVariant.Size.ONE_SIZE:
        return size
    rank = SIZE_ORDER.get(size)
    if rank is None:
        return size
    reverse_lookup = {
        value: key
        for key, value in SIZE_ORDER.items()
        if key != ProductVariant.Size.ONE_SIZE
    }
    shifted_rank = max(0, min(max(reverse_lookup), rank + delta))
    return reverse_lookup.get(shifted_rank, size)


def _numeric(profile: dict, key: str) -> float | None:
    value = profile.get(key)
    if value in (None, ""):
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _missing_profile_fields(profile: dict) -> list[str]:
    return [
        field_name
        for field_name in ("height_cm", "weight_kg", "preferred_fit")
        if profile.get(field_name) in (None, "")
    ]


def _product_prefers_bottom_size(product: Product) -> bool:
    category_slug = (getattr(product.category, "slug", "") or "").lower()
    return any(
        token in category_slug
        for token in ("pants", "cargo", "short", "denim", "bottom")
    )


def _derive_size_from_measurements(
    profile: dict, product: Product
) -> tuple[str | None, int]:
    score = 0
    measurement_ranks = []
    chest = _numeric(profile, "chest_cm")
    waist = _numeric(profile, "waist_cm")
    hips = _numeric(profile, "hips_cm")
    height = _numeric(profile, "height_cm")
    weight = _numeric(profile, "weight_kg")

    if chest is not None:
        score += 1
        if chest <= 88:
            measurement_ranks.append(0)
        elif chest <= 96:
            measurement_ranks.append(1)
        elif chest <= 104:
            measurement_ranks.append(2)
        elif chest <= 112:
            measurement_ranks.append(3)
        elif chest <= 120:
            measurement_ranks.append(4)
        else:
            measurement_ranks.append(5)

    if waist is not None:
        score += 1
        if waist <= 74:
            measurement_ranks.append(0)
        elif waist <= 82:
            measurement_ranks.append(1)
        elif waist <= 90:
            measurement_ranks.append(2)
        elif waist <= 98:
            measurement_ranks.append(3)
        elif waist <= 106:
            measurement_ranks.append(4)
        else:
            measurement_ranks.append(5)

    if hips is not None:
        score += 1
        if hips <= 90:
            measurement_ranks.append(0)
        elif hips <= 98:
            measurement_ranks.append(1)
        elif hips <= 106:
            measurement_ranks.append(2)
        elif hips <= 114:
            measurement_ranks.append(3)
        elif hips <= 122:
            measurement_ranks.append(4)
        else:
            measurement_ranks.append(5)

    if not measurement_ranks and height is not None and weight is not None:
        score += 1
        if height <= 165 or weight <= 55:
            measurement_ranks.append(0)
        elif height <= 172 or weight <= 65:
            measurement_ranks.append(1)
        elif height <= 179 or weight <= 75:
            measurement_ranks.append(2)
        elif height <= 185 or weight <= 85:
            measurement_ranks.append(3)
        elif height <= 191 or weight <= 95:
            measurement_ranks.append(4)
        else:
            measurement_ranks.append(5)

    if not measurement_ranks:
        return None, score

    rank = max(measurement_ranks)
    preference = profile.get("preferred_fit")
    product_fit = (product.fit or "").lower()
    if preference in {"relaxed", "oversized"} and rank < 5:
        rank += 1
    if preference == "slim" and rank > 0:
        rank -= 1
    if "oversized" in product_fit or "овер" in product_fit:
        if preference in {None, "", "regular", "slim"} and rank > 0:
            rank -= 1

    reverse_size_lookup = {
        0: ProductVariant.Size.XS,
        1: ProductVariant.Size.S,
        2: ProductVariant.Size.M,
        3: ProductVariant.Size.L,
        4: ProductVariant.Size.XL,
        5: ProductVariant.Size.XXL,
    }
    return reverse_size_lookup[rank], score


def _product_style_tokens(product: Product) -> set[str]:
    tokens = set()
    for raw_value in (
        product.name,
        product.description,
        product.fit,
        product.search_synonyms,
        product.season,
        getattr(product.category, "name", ""),
    ):
        text = (raw_value or "").lower()
        for token_group in STYLE_TOKENS.values():
            for token in token_group:
                if token in text:
                    tokens.add(token)
    for tag in product.tags.all():
        tokens.add((tag.slug or "").lower())
        tokens.add((tag.name or "").lower())
    return tokens


def _main_image_url(product: Product) -> str | None:
    image = next((item for item in product.images.all() if item.is_main), None)
    if image is None:
        image = next(iter(product.images.all()), None)
    if not image:
        return None
    return image.image.url if isinstance(image, ProductImage) and image.image else None


def _build_risk_summary(*, confidence: str, warnings: list[str], profile_ready: bool) -> tuple[str, list[str], str]:
    risk_reasons: list[str] = []
    risk_level = "low"
    fallback_action = "ready"

    if not profile_ready:
        risk_level = "high"
        fallback_action = "fill_fit_profile"
        risk_reasons.append("Профиль заполнен не полностью, поэтому точность рекомендации снижена.")

    if "recommended_size_out_of_stock" in warnings:
        risk_level = "high"
        fallback_action = "check_alternative_size"
        risk_reasons.append("Рекомендованный размер сейчас отсутствует на складе.")
    elif "closest_available_size_selected" in warnings:
        risk_level = "medium" if risk_level != "high" else risk_level
        fallback_action = "compare_neighbor_sizes"
        risk_reasons.append("Система выбрала ближайший размер, а не точное совпадение.")

    if "season_mismatch" in warnings or "style_mismatch" in warnings or "style_fit_mismatch" in warnings:
        if risk_level == "low":
            risk_level = "medium"
        fallback_action = "review_style_match"
        risk_reasons.append("Есть расхождение между товаром и предпочтениями пользователя.")

    if confidence in {"none", "low"} and risk_level == "low":
        risk_level = "medium"
        fallback_action = "review_measurements"
        risk_reasons.append("Рекомендация собрана с ограниченной уверенностью.")

    if not risk_reasons:
        risk_reasons.append("Существенных факторов риска для возврата не обнаружено.")

    return risk_level, risk_reasons, fallback_action


def _build_outfit_recommendation(product: Product, profile: dict) -> dict:
    budget_max = _numeric(profile, "budget_max_rub")
    preferred_style = (profile.get("preferred_style") or "").lower()

    related_products = (
        Product.objects.filter(
            related_to__from_product=product,
            status=Product.PublishingStatus.ACTIVE,
        )
        .select_related("category", "franchise")
        .prefetch_related("images", "tags")
        .distinct()
    )

    if not related_products.exists() and product.franchise_id:
        related_products = (
            Product.objects.filter(
                franchise_id=product.franchise_id,
                status=Product.PublishingStatus.ACTIVE,
            )
            .exclude(pk=product.pk)
            .select_related("category", "franchise")
            .prefetch_related("images", "tags")
            .order_by("-is_featured", "-created_at")[:6]
        )

    current_total = Decimal(product.base_price)
    items = []
    used_categories = {product.category_id}
    budget_status = "not_checked" if budget_max is None else "under_budget"
    budget_warning = ""

    for related_product in related_products:
        if related_product.category_id in used_categories:
            continue

        style_tokens = _product_style_tokens(related_product)
        reason = "Дополняет образ из той же капсулы."
        if preferred_style:
            expected_tokens = STYLE_TOKENS.get(preferred_style, ())
            if any(token in style_tokens for token in expected_tokens):
                reason = "Совпадает с выбранным стилем пользователя."

        next_total = current_total + Decimal(related_product.base_price)
        if budget_max is not None and float(next_total) > budget_max and items:
            budget_status = "over_budget"
            budget_warning = "Следующий товар выводит капсулу выше заданного бюджета."
            continue

        items.append(
            {
                "id": related_product.id,
                "name": related_product.name,
                "slug": related_product.slug,
                "category": related_product.category.name,
                "franchise": (
                    related_product.franchise.name
                    if related_product.franchise
                    else None
                ),
                "base_price": str(related_product.base_price),
                "main_image_url": _main_image_url(related_product),
                "reason": reason,
            }
        )
        used_categories.add(related_product.category_id)
        current_total = next_total

        if len(items) == 3:
            break

    if budget_max is not None and items:
        if float(current_total) > budget_max:
            budget_status = "over_budget"
            budget_warning = "Готовый образ превышает заданный бюджет."
        elif float(current_total) >= budget_max * 0.85:
            budget_status = "near_budget"
            budget_warning = "Готовый образ почти упирается в верхнюю границу бюджета."

    return {
        "items": items,
        "total_price": str(current_total) if items else None,
        "budget_status": budget_status,
        "budget_warning": budget_warning,
    }


def build_size_recommendation(
    *, product: Product, user, profile_override: dict | None = None
) -> dict:
    active_variants = _sorted_active_variants(product)
    if not active_variants:
        return {
            "recommended_size": None,
            "confidence": "none",
            "risk_level": "high",
            "profile_ready": False,
            "missing_profile_fields": [],
            "summary": "Сейчас у товара нет активных размеров.",
            "explanation": "Размерная рекомендация недоступна, потому что активные варианты отсутствуют.",
            "reasons": [],
            "risk_reasons": ["У товара нет активных размеров, поэтому подобрать размер нельзя."],
            "warnings": ["no_active_sizes"],
            "fallback_action": "wait_for_restock",
            "outfit": {"items": [], "total_price": None},
        }

    profile = dict(profile_override or {})
    if not profile:
        if not getattr(user, "is_authenticated", False):
            return DEFAULT_RECOMMENDATION.copy()
        profile = dict(getattr(user, "fit_profile", {}) or {})
    if not profile:
        return DEFAULT_RECOMMENDATION.copy()

    missing_fields = _missing_profile_fields(profile)
    profile_ready = len(missing_fields) == 0
    available_sizes = [variant.size for variant in active_variants]
    warnings: list[str] = []
    reasons: list[str] = []
    confidence = "low"

    size_key = (
        "bottoms_usual_size"
        if _product_prefers_bottom_size(product)
        else "tops_usual_size"
    )
    target_size = profile.get(size_key)
    if target_size:
        confidence = "medium"
        reasons.append(f"Опираемся на ваш обычный размер {target_size}.")

    if target_size is None:
        target_size, measurement_score = _derive_size_from_measurements(profile, product)
        if target_size:
            confidence = "high" if measurement_score >= 2 else "medium"
            reasons.append("Размер подобран по сохранённым меркам и параметрам фигуры.")

    fit_tendency = product.recommendation_fit_tendency

    if fit_tendency == Product.RecommendationFitTendency.RUNS_SMALL:
        target_size = _shift_size(target_size, 1)
        warnings.append("runs_small")
        reasons.append("Модель помечена как маломерящая, поэтому рекомендация сдвинута на размер вверх.")
    elif fit_tendency == Product.RecommendationFitTendency.RUNS_LARGE:
        target_size = _shift_size(target_size, -1)
        warnings.append("runs_large")
        reasons.append("Модель помечена как большемерящая, поэтому рекомендация сдвинута на размер вниз.")
    elif fit_tendency == Product.RecommendationFitTendency.OVERSIZED_DESIGN:
        warnings.append("oversized_by_design")
        reasons.append("Посадка заложена как оверсайз по дизайну изделия.")

    if target_size is None and ProductVariant.Size.ONE_SIZE in available_sizes:
        target_size = ProductVariant.Size.ONE_SIZE
        warnings.append("one_size_only")
        reasons.append("У товара one size, поэтому рекомендация ограничена одним вариантом.")

    if target_size is None:
        return {
            **DEFAULT_RECOMMENDATION,
            "missing_profile_fields": (
                missing_fields or DEFAULT_RECOMMENDATION["missing_profile_fields"]
            ),
        }

    recommended_size = _nearest_available_size(target_size, available_sizes)
    if recommended_size != target_size:
        warnings.append("closest_available_size_selected")
        reasons.append(
            f"Точного размера {target_size} нет в наличии, поэтому выбран ближайший активный вариант."
        )

    recommended_variant = next(
        variant for variant in active_variants if variant.size == recommended_size
    )
    variant_fit_tendency = (
        recommended_variant.recommendation_fit_tendency_override or fit_tendency
    )
    if recommended_variant.stock_quantity == 0:
        warnings.append("recommended_size_out_of_stock")
        confidence = "low"
        reasons.append(
            "Рекомендованный размер виден в витрине, но сейчас отсутствует на складе."
        )
    if (
        variant_fit_tendency == Product.RecommendationFitTendency.OVERSIZED_DESIGN
        and "oversized_by_design" not in warnings
    ):
        warnings.append("oversized_by_design")
        reasons.append("Конкретный вариант также отмечен как оверсайз по дизайну.")

    product_fit = (product.fit or "").lower()
    preferred_fit = (profile.get("preferred_fit") or "").lower()
    if ("oversized" in product_fit or "овер" in product_fit) and preferred_fit == "slim":
        warnings.append("style_fit_mismatch")
        reasons.append(
            "Модель задумана как более свободная, чем ваша предпочитаемая посадка."
        )
    if preferred_fit in {"relaxed", "oversized"}:
        reasons.append("Предпочтение более свободной посадки учтено в рекомендации.")

    preferred_season = (profile.get("preferred_season") or "").lower()
    product_season = (product.season or "").lower()
    if preferred_season and product_season and preferred_season != product_season:
        warnings.append("season_mismatch")

    preferred_style = (profile.get("preferred_style") or "").lower()
    if preferred_style:
        style_tokens = _product_style_tokens(product)
        expected_tokens = STYLE_TOKENS.get(preferred_style, ())
        if expected_tokens and not any(token in style_tokens for token in expected_tokens):
            warnings.append("style_mismatch")

    if product.recommendation_notes:
        reasons.append(product.recommendation_notes)
    if product.recommendation_body_shape_notes:
        reasons.append(product.recommendation_body_shape_notes)
    if recommended_variant.recommendation_notes_override:
        reasons.append(recommended_variant.recommendation_notes_override)

    if not profile_ready:
        confidence = "low"
        warnings.append("fit_profile_incomplete")

    if not reasons:
        reasons.append(
            "Рекомендация построена по сохранённому fit profile и доступным размерам."
        )

    risk_level, risk_reasons, fallback_action = _build_risk_summary(
        confidence=confidence,
        warnings=warnings,
        profile_ready=profile_ready,
    )

    return {
        "recommended_size": recommended_size,
        "confidence": confidence,
        "risk_level": risk_level,
        "profile_ready": profile_ready,
        "missing_profile_fields": missing_fields,
        "summary": (
            f"Рекомендуем размер {recommended_size}."
            if recommended_size
            else "Пока не удалось подобрать размер автоматически."
        ),
        "explanation": " ".join(reasons),
        "reasons": reasons,
        "risk_reasons": risk_reasons,
        "warnings": warnings,
        "fallback_action": fallback_action,
        "outfit": _build_outfit_recommendation(product, profile),
    }
