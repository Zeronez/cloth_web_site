# Branch protection plan (`main`)

## Goals

- Prevent breaking changes from landing without review.
- Ensure release quality and traceability.

## Recommended settings

- Require pull requests before merging.
- Require at least 1 approving review.
- Dismiss stale approvals when new commits are pushed.
- Require status checks to pass before merging:
  - backend tests (pytest)
  - frontend tests (jest)
  - lint checks (backend + frontend)
  - security scans (SAST/secret scan/image scan) if available in CI
- Require linear history (optional).
- Restrict who can push to `main` (no direct pushes).

## Tag/release permissions

- Only maintainers can create version tags.
- Releases should be created from `main` with a matching changelog entry.

