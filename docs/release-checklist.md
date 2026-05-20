# Release Checklist

## Before release

- confirm the target branch and commit hash;
- confirm GitHub Actions for that commit are green;
- review pending migrations and verify they are backward-compatible;
- confirm staging smoke checks or equivalent manual verification are complete;
- confirm provider credentials and env-file changes are ready;
- confirm backup freshness and restore confidence are within policy;
- confirm no unresolved dead-lettered notifications require intervention.

## Release execution

1. SSH to the production VPS.
2. Update the repository to the target commit.
3. Run:

```bash
bash deploy/scripts/preflight.sh
bash deploy/scripts/release.sh
```

4. Verify:
   - `https://<domain>/`
   - `https://<domain>/health/live/`
   - `https://<domain>/health/ready/`
   - admin login
   - a storefront catalog page

## After release

- inspect container status and logs;
- confirm Celery worker and beat are both running;
- verify no unexpected migration or startup errors appeared in logs;
- verify order checkout, payment return, and notification paths on a smoke
  basis when safe;
- annotate the deployment in the team log or release notes.

## If something looks wrong

- stop and evaluate whether this is an app-only rollback or a schema-level
  incident;
- use [deploy/scripts/rollback.sh](c:/Users/Всеволод/Desktop/cloth_web_site/deploy/scripts/rollback.sh)
  only for code rollback to a known good git ref;
- if the issue involves incompatible schema changes, use the dedicated database
  restore or migration rollback process rather than blindly redeploying older
  code.
