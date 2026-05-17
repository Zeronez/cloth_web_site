# Backup Encryption Runbook

## Goal

AnimeAttire must be able to restore commerce data without exposing backup
artifacts as an easier path to customer data or operational secrets.

This runbook defines the minimum production contract for encrypted backups of
the primary database and object storage.

## Protected assets

- PostgreSQL application database;
- object-storage media bucket contents and metadata;
- environment and deployment metadata needed for restore procedures.

## Minimum production requirements

### Database backups

- all PostgreSQL backups must be encrypted at rest;
- encryption should be provided by KMS-managed keys or the equivalent mechanism
  of the chosen backup platform;
- backup uploads must use TLS in transit;
- backup objects must be stored in a dedicated backup bucket or isolated backup
  prefix, not mixed with live uploads.

### Media backups

- the object-storage bucket used for product images and avatars must have
  default server-side encryption enabled;
- replicated or archived backup copies of media must remain encrypted at rest;
- backup transport must use TLS only;
- restore access must be limited to the operations group, not the application
  runtime user.

## Access control

- the application runtime credentials must not have permission to enumerate or
  restore backup archives;
- restore-capable credentials must be distinct from application credentials;
- access to backup destinations should be logged by the cloud or platform
  provider;
- decryption key access must be restricted to production operators and the
  owner.

## Retention baseline

- daily database backups: retain 35 days;
- monthly database backups: retain 12 months;
- media backup snapshots or replications: retain 35 days unless a stronger
  legal requirement applies.

These values must stay aligned with `docs/data-retention-policy.md`.

## Restore expectations

- run a restore drill on staging at least once per quarter;
- verify the restored database can boot the Django application and pass health
  checks;
- verify representative media objects can be read after restore;
- document restore duration and failures after each drill.

## Restore checklist

1. Provision isolated restore target.
2. Fetch encrypted database backup using restore-only credentials.
3. Restore PostgreSQL data.
4. Restore or mount matching media snapshot.
5. Start backend against the restored data.
6. Run health and smoke checks.
7. Record outcome and destroy temporary restore environment after validation.

## Non-goals

- this runbook does not yet define the exact backup vendor or cloud product;
- this runbook does not replace future staging automation for backup drills.
