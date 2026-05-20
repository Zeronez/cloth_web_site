# Uptime Checks

Цель: внешним мониторингом обнаруживать “сервис упал/не отвечает” быстрее, чем пользователи.

## Backend

### Liveness
- `GET /health/live/` — процесс жив.

### Readiness
- `GET /health/ready/` — готов обслуживать трафик (DB/Redis/Celery по настройкам).

### Webhook endpoint
- `POST /api/v1/payments/webhooks/<provider_code>/` — проверяем доступность маршрута (без реальной подписи).
  - Для uptime‑проверки лучше отдельный “пинг” роут, чтобы не засорять webhook логикой.

## Frontend
- `GET /healthz` — простая 200‑страница/route handler.
- `GET /` и `GET /catalog` — synthetic checks (раз в 5–10 минут).

## Триггеры алертов (старт)
- 2+ провала подряд (1–2 минуты) → warning
- 5+ провалов подряд (5–10 минут) → critical

