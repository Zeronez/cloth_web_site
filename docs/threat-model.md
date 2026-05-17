# AnimeAttire Threat Model

## Scope

This threat model covers the current AnimeAttire production surface that is
already present in the repository:

- customer authentication and session lifecycle;
- cart and checkout flows;
- payment session creation and payment webhooks;
- staff-facing Django admin workflows;
- file uploads for avatars and product images.

It is intended to be a living engineering document, not a one-time compliance
artifact.

## High-Value Assets

- customer accounts, addresses, and contact data;
- JWT refresh tokens and access tokens;
- order state, stock state, and payment state;
- webhook trust boundary and provider secrets;
- uploaded media storage;
- admin privileges and audit history.

## Trust Boundaries

1. Public browser to frontend.
2. Frontend to backend API with bearer JWT.
3. Backend to PostgreSQL and Redis.
4. External payment or delivery providers to webhook endpoints.
5. Staff browsers to Django admin.
6. User or staff file input to object storage-backed media handling.

## Entry Points

- `/api/v1/auth/*`
- `/api/v1/cart/*`
- `/api/v1/orders/checkout/`
- `/api/payments/webhooks/<provider>/`
- `/admin/*`
- avatar upload and product image upload model paths

## Threats by Surface

### 1. Authentication

Primary threats:

- credential stuffing and brute-force login attempts;
- stolen refresh tokens being replayed;
- object access bypass after authentication;
- sensitive token leakage through browser storage or logs.

Current controls:

- JWT rotation and blacklist on logout;
- object-level permissions for user-owned resources;
- frontend keeps access token memory-only and limits refresh token lifetime to
  `sessionStorage`;
- structured logging redacts token-like values.

Remaining gaps:

- admin 2FA is still open;
- formal secrets-management policy for environments is still open.

### 2. Checkout and Order Mutation

Primary threats:

- stock oversell through concurrent checkout;
- replay or duplicate checkout mutation;
- stale payment or delivery data causing inconsistent orders;
- malicious cart quantities or inactive SKU purchase attempts.

Current controls:

- transactional checkout with `select_for_update`;
- idempotency keys on checkout and payment creation;
- stock validation on cart and checkout paths;
- rollback tests for payment and delivery failure paths;
- provider recovery commands and timeout cleanup tasks.

Remaining gaps:

- full inventory reservation model with expiry is still open;
- broader load and abuse testing of checkout path is still open.

### 3. Payment Webhooks

Primary threats:

- forged provider callbacks;
- replayed webhook events;
- mismatched provider or order references;
- malformed payloads leading to partial state changes.

Current controls:

- provider-specific signature verification path;
- explicit bypass list only for local placeholder providers;
- idempotent webhook processing;
- conflict-safe status transition rules;
- reconciliation commands and audit/event history.

Remaining gaps:

- explicit replay/idempotency security test item remains open in the plan;
- live-provider operational credential rotation is still open.

### 4. Django Admin

Primary threats:

- privilege escalation from non-staff or wrong staff role;
- overexposed PII in admin audit history;
- destructive changes without traceability;
- operational mistakes on orders, payments, or stock.

Current controls:

- role-aware admin permissions;
- append-only audit log;
- redaction of sensitive audit snapshot and metadata fields;
- regular-user denial tests for admin routes;
- no destructive migration path without explicit migration safety plan.

Remaining gaps:

- richer operational dashboards remain incomplete.

### 5. File Uploads

Primary threats:

- non-image files disguised as images;
- oversized files or decompression-style image bombs;
- unsafe content types persisted into storage;
- user-controlled media becoming a persistence or delivery risk.

Current controls:

- strict image validation on avatar and product image save;
- extension, content-type, integrity, file-size, and pixel-count checks;
- upload validation tests;
- uploaded media persistence already covered by storage contract tests.

Remaining gaps:

- staff moderation flow for uploaded media is still open;
- downstream CDN and object-storage policy hardening is still open.

## Threat Severity Summary

Highest-risk current domains:

1. auth and token lifecycle;
2. checkout and stock mutation integrity;
3. payment webhook authenticity;
4. admin privilege misuse.

The repository now has concrete controls for all four, but admin 2FA and
broader secret handling still need implementation.

## Security Priorities After This Document

1. Add secret scanning in CI and keep false positives under control.
2. Add backend/frontend SAST.
3. Add admin 2FA rollout and enforcement.
4. Add secrets-management implementation and backup/restore drills.
