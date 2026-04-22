# Production Env Contract

This repository keeps the production contract in sync with `backend/config/settings/*` and `.env.example`.
Values here are examples only. Do not reuse placeholders in production.

## Required in production

- `DJANGO_SETTINGS_MODULE`: should point to `config.settings.production`.
- `SECRET_KEY`: Django signing key.
- `DATABASE_URL`: PostgreSQL connection string.
- `REDIS_URL`: Redis cache URL.
- `CELERY_BROKER_URL`: Redis URL for Celery broker.
- `CELERY_RESULT_BACKEND`: Redis URL for Celery result backend.
- `ALLOWED_HOSTS`: comma-separated Django hosts.
- `CSRF_TRUSTED_ORIGINS`: comma-separated absolute origins.
- `CORS_ALLOWED_ORIGINS`: comma-separated absolute origins.

## Postgres compose inputs

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

`DATABASE_URL` is derived from these values in `docker-compose.yml`.

## JWT

- `SIMPLE_JWT_ACCESS_TOKEN_LIFETIME_MINUTES`
- `SIMPLE_JWT_REFRESH_TOKEN_LIFETIME_DAYS`
- `SIMPLE_JWT_ROTATE_REFRESH_TOKENS`
- `SIMPLE_JWT_BLACKLIST_AFTER_ROTATION`

## Email

These are used by Django email settings and are required when you switch to SMTP in production.

- `EMAIL_BACKEND`
- `DEFAULT_FROM_EMAIL`
- `SERVER_EMAIL`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_USE_TLS`
- `EMAIL_USE_SSL`
- `EMAIL_TIMEOUT`

## S3 / object storage

These are used when media is routed to S3 or an S3-compatible service.

- `AWS_STORAGE_BUCKET_NAME`
- `AWS_S3_ENDPOINT_URL`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_S3_REGION_NAME`

## Local compose helpers

- `BACKEND_PORT`
- `FRONTEND_PORT`
- `NEXT_PUBLIC_API_URL`
