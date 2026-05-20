# ADR 0001: Platform architecture

## Status

Accepted — 2026-05-20

## Context

AnimeAttire is an ecommerce storefront for Russia-first launch. The product requires:

- catalog browsing and filtering
- cart and checkout
- order lifecycle and fulfillment states
- staff/admin operations
- reliable backend workflows (async tasks, idempotency)
- a modern storefront UI

## Decision

- **Backend**: Django + Django REST Framework, with PostgreSQL as primary DB.
- **Async**: Celery with Redis as broker/result backend for background jobs (timeouts, notifications, reconciliation).
- **API**: Versioned REST API under `/api/v1/`.
- **Schema**: OpenAPI via `drf-spectacular`, published at `/api/v1/schema/` and docs at `/api/v1/swagger/` + `/api/v1/redoc/`.
- **Frontend**: Next.js (App Router) + TypeScript + Tailwind, with React Query for data fetching and Zustand for local state.
- **Deployment**: Docker-first; compose-based deployments supported in repo (local and VPS flows).

## Consequences

- Backend correctness relies on transactional boundaries and idempotency for checkout/payment/delivery workflows.
- API compatibility must be maintained via explicit versioning and schema checks.
- Frontend should treat API as the source of truth and use schema-driven typing over time.

