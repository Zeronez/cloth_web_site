# Release versioning policy and changelog

## Versioning

Use **SemVer**: `MAJOR.MINOR.PATCH`.

- `PATCH`: bugfixes, security patches, internal refactors, no API breaking changes.
- `MINOR`: new features, additive API changes, new pages/flows.
- `MAJOR`: breaking API changes, incompatible data migrations, major UX changes.

Pre-1.0 rules:

- Until `1.0.0`, breaking changes may increment `MINOR` if communicated clearly in the changelog.

## Changelog

- Keep a `CHANGELOG.md` at repo root.
- Follow “Keep a Changelog” structure:
  - `Unreleased`
  - per release version sections with date
  - `Added/Changed/Deprecated/Removed/Fixed/Security`

## Tagging and releases

- Each release corresponds to a git tag: `vX.Y.Z`.
- Release steps (high level):
  1. Update `CHANGELOG.md` (move entries from `Unreleased` to a version section).
  2. Run CI (or locally run smoke tests).
  3. Tag and push tag: `git tag vX.Y.Z && git push origin vX.Y.Z`.

