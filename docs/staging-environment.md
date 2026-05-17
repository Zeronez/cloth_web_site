# Staging Environment

## Goal

AnimeAttire staging is the pre-production environment used for restore drills,
integration verification, and release-candidate smoke checks without touching
live production data.

## What is included

- PostgreSQL 16
- Redis 7
- Django backend
- Celery worker
- Next.js frontend
- MinIO as an S3-compatible media target

## Local staging compose

Use:

```bash
docker compose -f docker-compose.staging.yml --env-file .env.staging.example up --build
```

Default local staging endpoints:

- frontend: `http://localhost:3001`
- backend: `http://localhost:8001`
- postgres: `localhost:5434`
- redis: `localhost:6380`
- minio api: `http://localhost:9000`
- minio console: `http://localhost:9001`

## Intended uses

- quarterly backup restore drill rehearsal
- payment and delivery integration rehearsal with staging-safe credentials
- smoke validation of migrations before production release
- manual QA for storefront, admin, and media storage

## Boundaries

- staging must not reuse production secrets;
- staging backup artifacts must stay separate from production backup storage;
- staging media bucket and prefixes must remain separate from production media;
- staging may use provider sandbox credentials or local provider-shaped fixtures.

## Follow-up work

- add infra-managed staging deployment if we move beyond compose-based staging;
- add scripted restore-drill checklist execution on top of this environment;
- add MinIO-backed CI coverage for media flows.
