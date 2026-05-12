# Migration Safety Policy

AnimeAttire treats schema-contraction migrations as an operational change, not a routine refactor.

## Protected operations

The CI safety gate blocks new migrations that use destructive or high-risk operations such as:

- `AlterField`
- `AlterModelTable`
- `DeleteModel`
- `RemoveConstraint`
- `RemoveField`
- `RemoveIndex`
- `RenameField`
- `RenameModel`
- `RunSQL`
- `SeparateDatabaseAndState`

## Required declaration

Any new migration that contains one of those operations must declare a module-level
`MIGRATION_SAFETY_PLAN` dictionary with these non-empty keys:

- `ticket`
- `summary`
- `backfill`
- `deploy_strategy`
- `rollback`

This keeps the operational intent attached to the migration itself, which is the exact artifact reviewed in GitHub and executed in CI/CD.

## Legacy baseline

Pre-policy destructive migrations that already exist in the repository are grandfathered by an explicit allowlist inside `audit.migration_safety`.
New destructive migrations must comply with the policy.

## CI enforcement

`Production CI` runs:

```bash
python manage.py checkmigrationsafety
```

before `python manage.py migrate --noinput`.

That means a migration without an attached backfill and rollback plan cannot reach the test database, Docker build stage, or production promotion path.
