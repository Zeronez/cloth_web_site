# Sentry Setup (Backend + Frontend)

Цель: получить ошибки и перформанс‑трейсы из продакшена, быстро находить регрессии после релизов.

## Backend (Django)

Рекомендуется `sentry-sdk` с интеграциями Django + Celery.

### Переменные окружения
- `SENTRY_DSN` — DSN проекта (backend).
- `SENTRY_ENVIRONMENT` — `production` / `staging`.
- `SENTRY_TRACES_SAMPLE_RATE` — например `0.05` (5%).
- `SENTRY_PROFILES_SAMPLE_RATE` — опционально, например `0.0` или `0.01`.

### Теги
- `release` — берём из `GIT_SHA`/версии релиза.
- `server_name` — hostname.

### PII
- Не отправлять ПДн (email/телефон/адрес) в события.
- Для user‑контекста — только `user_id` (если нужно) или анонимизированные данные.

## Frontend (Next.js)

Варианты:
1) `@sentry/nextjs` (рекомендуется) — автосборка sourcemaps и трассировка.
2) Минимально: `@sentry/browser` + ручной `captureException` из `app/error.tsx`.

### Переменные окружения
- `NEXT_PUBLIC_SENTRY_DSN` — DSN проекта (frontend).
- `SENTRY_AUTH_TOKEN` — только для CI/сборки (если загружать sourcemaps).
- `SENTRY_ORG`, `SENTRY_PROJECT`
- `SENTRY_RELEASE`

### Что проверить перед продом
- Sourcemaps загружаются (ошибки в Sentry показывают исходные файлы).
- Sampling настроен (не льём 100% трафика).
- В событиях нет ПДн.

