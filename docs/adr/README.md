# Architecture Decision Records (ADR)

This folder stores **Architecture Decision Records** for AnimeAttire.

## Why ADRs exist

ADRs capture **what we decided**, **why**, and **what alternatives** were considered.
They are a lightweight source of truth for onboarding and future changes.

## Format

- One decision per file.
- Filename: `NNNN-short-title.md` (e.g. `0001-platform-architecture.md`).
- Keep it short and explicit: context → decision → consequences.

## Workflow

1. Create a new ADR for any decision that affects:
   - architecture, service boundaries, or data model
   - auth/session strategy
   - payments/delivery integration approach
   - deployment model or infra dependencies
   - API versioning/compatibility policy
2. Submit as PR.
3. Never rewrite history silently: create a new ADR that supersedes the previous one.

