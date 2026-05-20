# Dashboards (Grafana / Sentry)

Цель: быстрый “операторский” обзор здоровья продукта.

## 1) API overview
- RPS по сервисам/роутам (с агрегацией).
- p50/p95/p99 latency.
- 4xx/5xx rate.
- Top endpoints by latency / error.

## 2) Checkout & Payments
- Кол-во созданных заказов (в минуту/час).
- Доля успешных оплат / failed/cancelled/expired.
- Время от создания заказа до `payment_succeeded`.
- Ошибки вебхуков (signature, parsing, provider failures).

## 3) Celery
- Длина очередей.
- Время выполнения задач (histogram).
- Кол-во ретраев / dead-letter (если есть).
- Worker up/down, heartbeats.

## 4) DB / Cache
- Connections, locks.
- Slow queries (count + top N).
- Cache hit rate (Redis).

## 5) Frontend
- Error rate (Sentry).
- Web Vitals (если собираем).
- Uptime/TTFB для ключевых страниц.

