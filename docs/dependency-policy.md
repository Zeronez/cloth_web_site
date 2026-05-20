# Dependency update policy and lockfile strategy

## Goals

- Keep dependencies reasonably fresh without destabilizing production.
- Ensure builds are deterministic across machines and CI.
- Make security updates fast and low-risk.

## Lockfiles

- **Frontend**: `frontend/package-lock.json` is the source of truth and must be committed.
- **Backend**: dependencies are pinned in:
  - `backend/requirements.txt` (runtime)
  - `backend/requirements-dev.txt` (dev/test)
  - `backend/requirements.in` and `backend/requirements-dev.in` are the inputs.

## Update cadence

- Weekly: safe minor/patch updates.
- Monthly: deliberate updates that may require code changes.
- Security: ASAP hotfix updates (out of band).

## Update rules

- Avoid large version jumps in one PR.
- Prefer patch/minor bumps; major bumps require explicit review and a rollback plan.
- Any update that touches auth/checkout/payments/delivery requires running the full test suite.

## Automation (recommended)

- Use Dependabot for:
  - `pip` (backend) weekly
  - `npm` (frontend) weekly
- Keep PRs small (group by ecosystem).

