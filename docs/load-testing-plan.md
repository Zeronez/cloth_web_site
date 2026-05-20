# Load Testing Plan (Catalog + Checkout)

Цель: поймать деградации до продакшена и оценить headroom инфраструктуры.

## Инструмент
- k6 (рекомендуется) или Locust.

## Сценарии
1) Каталог browsing
   - `GET /api/v1/categories/`
   - `GET /api/v1/products/?page=1&page_size=24`
   - фильтры: `category`, `size`, `in_stock`, `ordering`
2) Карточка товара
   - `GET /api/v1/products/<slug>/`
3) Корзина
   - создать guest cart, добавить/обновить/удалить item
4) Checkout
   - quote totals, создать order, payment session
5) Webhooks
   - имитация валидных webhook payloads (в тестовой среде)

## Нагрузочные профили
- Smoke: 1–5 VU, 5 минут.
- Baseline: 20–50 VU, 15 минут.
- Stress: рост до отказа (step‑load).
- Soak: 10–20 VU, 1–2 часа (утечки памяти/коннекций).

## Метрики успеха
- p95 latency на ключевых endpoint’ах.
- error rate (5xx).
- время на checkout end‑to‑end.
- DB load (connections, locks).
- Celery lag.

