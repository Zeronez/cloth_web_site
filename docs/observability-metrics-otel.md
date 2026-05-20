# Metrics / OpenTelemetry

Цель: видеть SLO‑метрики (latency, error rate), а также узкие места (DB, Celery, внешние провайдеры).

## Минимальный набор метрик

Backend:
- HTTP latency p50/p95/p99 по роутам (или группам роутов).
- HTTP 4xx/5xx rate.
- Количество запросов к платежным вебхукам + доля ошибок.
- Celery: длина очередей, время выполнения задач, процент ретраев.
- DB: slow queries, pool saturation.

Frontend:
- Ошибки JS (error rate).
- Web Vitals (LCP/CLS/INP).

## Реализация (варианты)

### A) Prometheus + Grafana
- Django: `django-prometheus` или кастомный `/metrics`.
- Celery: `celery-exporter` или экспортер брокера (Redis).
- Nginx: exporter (опционально).

### B) OpenTelemetry (OTel) + OTLP collector
- Backend: OTel SDK + автоинструментация (Django, requests, DB).
- Frontend: отправка web‑vitals/ошибок отдельно (Sentry часто проще).

## Рекомендованные SLO (старт)
- API: p95 < 400ms для чтения каталога, p95 < 800ms для checkout.
- Error rate: < 0.5% 5xx.
- Celery: критические задачи (подтверждение заказа) < 30s.

