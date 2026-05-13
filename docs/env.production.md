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

Production CORS is fail-closed: wildcard origins and credentialed cross-origin
cookies are disabled. The frontend should call `/api/v1/` with JWT bearer
tokens from origins listed in `CORS_ALLOWED_ORIGINS`.
Because bearer tokens are used today, cross-origin browser credentials remain
disabled. A future HttpOnly-cookie refresh-token strategy should be designed as
a separate auth change with explicit CSRF handling.

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

Current auth transport is a no-cookie bearer JWT contract:

- Login returns `access` and `refresh` in JSON from `/api/v1/auth/token/`.
- Protected API requests send `Authorization: Bearer <access>`.
- Refresh uses `/api/v1/auth/token/refresh/` with the refresh token in JSON.
- Logout uses `/api/v1/auth/logout/` and blacklists the refresh token server-side.
- The browser must not send credentialed CORS requests for auth in this mode.
- Frontend access tokens are memory-only; the refresh token is limited to
  `sessionStorage` so it does not survive a closed browser session.

Refresh rotation and blacklist-after-rotation must remain enabled in production.
Moving refresh tokens into HttpOnly cookies is a separate auth migration because
it requires credentialed CORS, cookie domain policy, and CSRF tests.

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

## Payment webhook signatures

These define which providers may bypass signature checks and which providers must present a valid HMAC signature.

- `PAYMENT_WEBHOOK_BYPASS_PROVIDERS`
- `PAYMENT_WEBHOOK_SECRETS_JSON`
- `PAYMENT_WEBHOOK_SIGNATURE_HEADERS_JSON`

## Payment redirect session contracts

These define sandbox or hosted checkout confirmation URLs for redirect-based providers.

- `PAYMENT_PROVIDER_CONFIRMATION_URLS_JSON`
- `PAYMENT_PROVIDER_RETURN_BASE_URL`
- `PAYMENT_PROVIDER_STATUS_OVERRIDES_JSON`

## Delivery tracking sandbox contracts

These define sandbox-like tracking responses for provider-shaped shipping adapters.

- `DELIVERY_PROVIDER_TRACKING_OVERRIDES_JSON`
- `DELIVERY_PICKUP_POINT_OVERRIDES_JSON`

## Local compose helpers

- `BACKEND_PORT`
- `FRONTEND_PORT`
- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_API_PREFIX`

## Celery delivery policy

These settings control retry and dead-letter behavior for transactional
notifications:

- `CELERY_TASK_ACKS_LATE`
- `CELERY_TASK_ACKS_ON_FAILURE_OR_TIMEOUT`
- `CELERY_TASK_REJECT_ON_WORKER_LOST`
- `CELERY_TASK_TRACK_STARTED`
- `CELERY_TASK_DEFAULT_QUEUE`
- `CELERY_NOTIFICATION_QUEUE`
- `CELERY_WORKER_PREFETCH_MULTIPLIER`
- `CELERY_NOTIFICATION_MAX_RETRIES`
- `CELERY_NOTIFICATION_RETRY_BACKOFF_SECONDS`
- `CELERY_NOTIFICATION_RETRY_MAX_SECONDS`
- `CELERY_NOTIFICATION_PROCESSING_LEASE_SECONDS`
- `PAYMENT_SESSION_TIMEOUT_MINUTES`
- `PAYMENT_EXPIRATION_BATCH_SIZE`
- `CART_GUEST_TTL_HOURS`
- `CART_CLEANUP_BATCH_SIZE`

Current production contract:

- task acknowledgements stay late so worker loss does not silently drop work;
- failures/timeouts are not acknowledged as success;
- order-confirmation delivery is routed through the dedicated
  `CELERY_NOTIFICATION_QUEUE`;
- notification tasks retry with bounded exponential backoff;
- a notification row holds a short processing lease so duplicate workers back
  off instead of sending the same email concurrently;
- retryable exhaustion moves the logical notification into a dead-lettered
  state that requires operator review;
- Redis is still the broker here, so dead-letter handling is implemented as an
  application-level `NotificationLog.dead_lettered_at` marker plus append-only
  `NotificationAttempt` history, not a broker-native DLX/DLQ;
- delivered notifications remain idempotent for the same
  `order/type/channel` key and do not send duplicate customer emails after a
  successful delivery.
- payment sessions expire on a bounded timer so stale unpaid orders can be
  cancelled and their stock returned by background processing;
- guest carts expire after a bounded inactivity window so abandoned anonymous
  carts do not accumulate forever in the production database.
