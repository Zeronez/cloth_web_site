# Zero-Downtime Release Strategy

## Goal

AnimeAttire runs on a single VPS, so true no-impact blue/green deployment is
not realistic without extra capacity. The current strategy is therefore
`zero-downtime-ish`: keep public ingress alive, apply only backward-compatible
schema changes, and rotate application services fast enough that customer impact
 stays minimal.

## Principles

- Caddy stays up during application refresh.
- Schema changes must be backward-compatible before code rollout.
- Migrations and `collectstatic` must run as one-off release steps, not on every
  backend container boot.
- Backend, frontend, Celery worker, and Celery beat are refreshed explicitly
  after the pre-release data steps complete.
- Destructive or irreversible migrations must wait for the dedicated migration
  rollback drill plan item.

## Release flow

1. Fetch the target git revision on the server.
2. Run preflight validation:

```bash
bash deploy/scripts/preflight.sh
```

3. Run the release script:

```bash
bash deploy/scripts/release.sh
```

The release script performs:

- `docker compose config` validation;
- one-off `python manage.py migrate --noinput`;
- one-off `python manage.py collectstatic --noinput`;
- `docker compose up -d --build --no-deps backend frontend celery celery-beat caddy`;
- backend readiness verification;
- frontend readiness verification.

## Why migrations moved out of normal startup

Automatic migrations on every backend container restart are convenient for the
first bring-up, but they are a poor fit for controlled production releases:

- restarts become coupled to schema mutation;
- rollback becomes murkier;
- multiple backend starts can race around operational intent;
- release health checks become harder to reason about.

Running migrations as an explicit release step gives a much clearer operational
boundary.

## Guardrails

- keep migrations additive first: new columns nullable, new code tolerant of
  old and new shapes during rollout;
- postpone column drops, renames, or semantic rewrites until a later cleanup
  release;
- if a release needs a destructive schema move, schedule it under the separate
  migration rollback drill process rather than this fast-path release flow.

## What this does not promise

- it does not guarantee zero TCP reconnects for every client;
- it does not provide spare-capacity rolling updates across multiple backend
  replicas;
- it does not solve destructive migration rollback.

For the current single-VPS target, this is the honest production-safe baseline.
