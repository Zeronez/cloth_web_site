TAG_TRANSLATIONS = {
    "new-drop": "Новый дроп",
    "bestseller": "Бестселлер",
    "limited": "Лимитированная серия",
    "streetwear": "Стритвир",
    "oversized": "Оверсайз",
    "collector": "Коллекционная позиция",
    "essentials": "База гардероба",
    "layering": "Для многослойных образов",
}


def get_tag_label(slug: str, fallback_name: str) -> str:
    return TAG_TRANSLATIONS.get(slug, fallback_name)


def get_matching_tag_slugs(query: str) -> list[str]:
    normalized_query = query.strip().casefold()
    if not normalized_query:
        return []

    matched_slugs: list[str] = []
    for slug, label in TAG_TRANSLATIONS.items():
        candidates = (
            slug.casefold(),
            slug.replace("-", " ").casefold(),
            label.casefold(),
        )
        if any(
            normalized_query in candidate or candidate in normalized_query
            for candidate in candidates
        ):
            matched_slugs.append(slug)
    return matched_slugs
