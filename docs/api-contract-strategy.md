# API contract documentation strategy

## Goals

- Make the API **discoverable** (interactive docs).
- Make the API **stable** (versioning + consistent error shapes).
- Make the API **typed** (frontend types aligned with OpenAPI).

## Current implementation

- API versioning: `/api/v1/`.
- Schema + docs (backend):
  - `GET /api/v1/schema/` — OpenAPI schema
  - `GET /api/v1/swagger/` — Swagger UI
  - `GET /api/v1/redoc/` — ReDoc

## Contract rules

1. All public endpoints must appear in the OpenAPI schema.
2. Backward-incompatible changes require:
   - either new fields only (additive), or
   - a new API version (`/api/v2/`) when breaking changes are unavoidable.
3. Error response shapes must remain stable and code-driven (`error.code`, `error.details`, ids).

## Frontend typing plan

Preferred long-term approach:

- Generate TypeScript types from OpenAPI (e.g. `openapi-typescript`).
- Use generated request/response types in `frontend/lib/api.ts`.

Interim approach:

- Keep manual types in the frontend, but ensure they match schema by periodic checks.

## CI gates (recommended)

- Generate OpenAPI schema in CI and store as artifact (or compare to committed `schema.json`).
- Validate that the frontend API client types are compatible with the schema.
- Add a backward-compatibility check step for schema diffs.

