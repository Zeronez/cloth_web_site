# Database Backup Schedule and Restore Drill

## Goal

AnimeAttire must be able to recover the primary PostgreSQL database within a
predictable operational window and prove that recovery regularly works in a
non-production environment.

This document defines the baseline backup schedule and the quarterly restore
drill expected before production launch.

## Backup schedule baseline

### Daily backups

- run one full logical or snapshot-based PostgreSQL backup every 24 hours;
- retain daily backups for 35 days;
- store backups only in encrypted backup storage described in
  `docs/backup-encryption-runbook.md`.

### Monthly backups

- preserve one monthly recovery point for 12 months;
- monthly recovery points must be stored in the same encrypted backup domain or
  an equivalent archival tier with the same restore-access restrictions.

### Recovery metadata

Each backup record should include:

- backup timestamp in UTC;
- database engine/version;
- source environment name;
- backup type;
- retention class (`daily` or `monthly`);
- checksum or provider integrity marker;
- restoration instructions or artifact reference.

## Restore drill cadence

- perform one restore drill per quarter;
- run the drill against staging or an isolated restore target, never against
  live production resources;
- keep a written outcome log with date, operator, recovery source, duration,
  and follow-up actions.

## Restore drill procedure

1. Provision isolated PostgreSQL target for the drill.
2. Restore the selected encrypted backup.
3. Point backend settings at the restored database.
4. Run Django migrations check without introducing new schema drift.
5. Start the backend application.
6. Run health endpoints and a short smoke path:
   - liveness;
   - readiness;
   - login/token endpoint;
   - catalog list endpoint.
7. Record restore duration, errors, and any data mismatch found.
8. Destroy temporary restore infrastructure after validation.

## Acceptance criteria for a successful drill

- restored database boots the Django app successfully;
- `manage.py check` passes on the restored environment;
- health endpoints return success;
- representative catalog and account-related queries succeed;
- operators can identify the exact backup artifact used;
- access to the restored environment is limited to the drill participants.

## Failure handling

If a restore drill fails:

- freeze any production-readiness claim for backup recovery;
- open an operational issue with root cause and corrective action;
- repeat the drill after the fix instead of waiting for the next quarter.

## Relationship to the plan

This document closes the scheduling and drill-definition part of:

- `Add database backup schedule and restore drill`

The executable staging automation and the final manual acceptance item
`Backup and restore drill on staging` remain separate follow-up tasks in
`ORCHESTRATION_PLAN.txt`.
