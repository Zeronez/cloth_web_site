# Media Backup Strategy

## Goal

AnimeAttire must preserve product media and any customer-uploaded media that is
still legitimately required by business workflows, while avoiding uncontrolled
growth of orphaned files.

This document defines the baseline strategy for live media, backup copies, and
future orphan cleanup.

## Covered media classes

- product images stored through the configured S3-compatible storage;
- user avatars while the related account remains active;
- storage metadata needed to map backed-up objects back to application records.

## Live-storage expectations

- the live media bucket must use private access by default;
- the bucket must have default server-side encryption enabled;
- uploads and reads must use HTTPS/TLS only;
- direct backup access must not be granted to the application runtime
  credentials.

## Backup strategy

### Primary approach

- use bucket replication, versioned snapshots, or scheduled object backup in a
  dedicated encrypted backup target;
- keep backup media in a logically separate bucket, prefix, or storage account
  from the live storefront bucket;
- use restore-only credentials for backup retrieval.

### Retention baseline

- retain media backup snapshots or replicated copies for 35 days;
- extend retention only when a stronger product or legal requirement appears;
- keep retention aligned with `docs/data-retention-policy.md` and
  `docs/backup-encryption-runbook.md`.

## Lifecycle rules by media type

### Product images

- retain while the product is active;
- retain while the product is archived and still part of operational history;
- future orphan-cleanup automation should remove detached product files after a
  30-day grace period.

### User avatars

- retain only while the account remains active;
- delete during account deletion flow, which is already implemented.

## Restore expectations

- the team must be able to restore representative product media during the
  quarterly backup drill window;
- restored media should be validated by reading real object URLs or storage keys
  from a restored database snapshot;
- media restore testing should cover at least one product image and one avatar
  fixture when available.

## Follow-up implementation items

- add infrastructure automation for bucket replication or snapshot scheduling;
- add orphaned-media detection and cleanup job;
- add staging restore verification for representative media files;
- add CI coverage with MinIO or another S3-compatible emulator.

## Relationship to the plan

This document closes the strategy-definition part of:

- `Add media backup strategy`

Infrastructure automation and executable restore validation remain separate
follow-up tasks in `ORCHESTRATION_PLAN.txt`.
