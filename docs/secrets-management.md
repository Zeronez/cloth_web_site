# Secrets Management

## Goal

AnimeAttire secrets must stay out of git history, developer machines by
default, and public CI logs while remaining practical for staging and
production operations.

## Secret sources by environment

### Local development

- local-only `.env` files may be used on a developer workstation;
- development placeholders must never be copied into staging or production;
- developer `.env` files remain untracked.

### CI

- GitHub Actions protected secrets belong in GitHub Environments or repository
  secrets depending on scope;
- staging credentials should live in a `staging` environment;
- production credentials should live in a `production` environment with manual
  approval and restricted maintainers;
- CI must never print raw secret values to logs.

### Runtime production

- the canonical runtime source is `/etc/animeattire/production.env`;
- the file must be owned by `root` and readable only by root or the deployment
  operator group;
- secrets are injected into containers through `docker compose --env-file`;
- production secrets must not be committed into compose files, `.env.example`,
  or shell history.

## Required production secret groups

- Django signing key: `SECRET_KEY`
- database credential: `POSTGRES_PASSWORD`
- SMTP credential: `EMAIL_HOST_PASSWORD`
- payment webhook secrets: `PAYMENT_WEBHOOK_SECRETS_JSON`
- object storage access keys when S3-compatible storage is enabled:
  `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

## Rotation policy

- rotate `SECRET_KEY` only through a planned maintenance procedure because it
  invalidates existing sessions and signed tokens;
- rotate SMTP and webhook secrets at least annually or immediately after
  suspected exposure;
- rotate database and object-storage credentials whenever an operator with
  access leaves the project;
- validate secret changes first in staging when the provider offers sandbox
  credentials.

## Logging and handling rules

- never paste raw secrets into issues, pull requests, or chat transcripts;
- never commit a filled production env file;
- CLI commands that reference secret files should point to file paths, not
  inline secret values;
- rely on existing repository secret scanning and CI secret scanning as a
  safety net, not as the primary control.

## GitHub environment baseline

Recommended GitHub Environments:

- `staging`
- `production`

Recommended controls for `production`:

- required reviewers before deploy workflows can read environment secrets;
- restricted branch policy to `main`;
- deploy workflow scoped to maintainers only;
- environment-specific variables for non-secret values such as domain names.

## Follow-up path

If the project outgrows env-file based runtime secret delivery, the next step
should be a managed secret backend such as cloud secret manager, Vault, or
Doppler. That migration should preserve the same secret contract documented in
[production.env.example](c:/Users/Всеволод/Desktop/cloth_web_site/production.env.example).
