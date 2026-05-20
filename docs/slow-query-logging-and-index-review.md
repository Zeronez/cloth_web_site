# Slow Query Logging & Index Review

Цель: найти и стабильно контролировать “дорогие” запросы, которые ломают p95 и приводят к таймаутам.

## План работ
- Включить логирование slow queries (PostgreSQL):
  - `log_min_duration_statement` (например, 200–500ms на старте)
  - `log_statement` не включать глобально в проде
- Регулярно собирать топ запросов (pg_stat_statements).
- Для топ N запросов:
  - снять `EXPLAIN (ANALYZE, BUFFERS)`
  - проверить индексы, порядок фильтров, сортировку
  - проверить N+1 (Django `select_related/prefetch_related`)

## Чеклист индексов (commerce)
- `orders(order_status, created_at)`
- `payments(status, created_at)` и `payments(order_id)`
- `catalog_product(status, created_at)` и фильтруемые поля каталога
- `cart_cart(updated_at)` для cleanup

## Релизный процесс
- Перед релизом: прогнать критические сценарии и снять p95.
- После релиза: сравнить latency и DB load, откат при деградации.

