# Production VPS Deployment

## Deployment target

AnimeAttire production target is a single Linux VPS with Docker Engine,
Docker Compose, and Caddy as the public TLS reverse proxy.

This is the current recommended deployment shape for the project because it:

- keeps the runtime close to the already tested container stack;
- gives automatic HTTPS and certificate renewal;
- keeps backend, worker, database, Redis, and storefront in one reproducible
  compose deployment;
- is small enough to operate without introducing Kubernetes before the product
  actually needs it.

## Runtime topology

- `caddy`: public ingress on ports `80/443`, automatic TLS, static/media
  serving, reverse proxy to backend/frontend
- `frontend`: Next.js standalone server
- `backend`: Django API/admin application
- `celery`: async worker
- `postgres`: primary relational database
- `redis`: cache, throttling, and Celery broker/result backend

## Files used

- [docker-compose.vps.yml](c:/Users/Всеволод/Desktop/cloth_web_site/docker-compose.vps.yml)
- [deploy/caddy/Caddyfile](c:/Users/Всеволод/Desktop/cloth_web_site/deploy/caddy/Caddyfile)
- [deploy/systemd/animeattire.service](c:/Users/Всеволод/Desktop/cloth_web_site/deploy/systemd/animeattire.service)
- [production.env.example](c:/Users/Всеволод/Desktop/cloth_web_site/production.env.example)
- [docs/secrets-management.md](c:/Users/Всеволод/Desktop/cloth_web_site/docs/secrets-management.md)

## One-time server bootstrap

1. Provision a VPS with Ubuntu 24.04 LTS or another current Linux distro.
2. Install Docker Engine and Compose plugin.
3. Create a dedicated app directory:

```bash
sudo mkdir -p /opt/animeattire
sudo chown "$USER":"$USER" /opt/animeattire
```

4. Clone the repository into `/opt/animeattire`.
5. Create `/etc/animeattire/production.env` from `production.env.example`.
6. Restrict secret file permissions:

```bash
sudo mkdir -p /etc/animeattire
sudo chown root:root /etc/animeattire
sudo chmod 700 /etc/animeattire
sudo chmod 600 /etc/animeattire/production.env
```

## First deploy

```bash
cd /opt/animeattire
docker compose --env-file /etc/animeattire/production.env -f docker-compose.vps.yml up -d --build
```

What this does today:

- starts PostgreSQL and Redis with persistent named volumes;
- runs Django migrations during backend startup;
- collects Django static assets into a shared volume served by Caddy;
- starts the Celery worker;
- starts the Next.js storefront;
- obtains and renews TLS certificates through Caddy automatically.

## Reverse proxy behavior

Caddy handles these routes:

- `/api/*` -> Django backend
- `/admin/*` -> Django admin
- `/static/*` -> shared Django static volume
- `/media/*` -> shared media volume when local media is used
- everything else -> Next.js frontend

## Systemd management

Install the provided unit:

```bash
sudo cp deploy/systemd/animeattire.service /etc/systemd/system/animeattire.service
sudo systemctl daemon-reload
sudo systemctl enable animeattire.service
sudo systemctl start animeattire.service
```

Useful commands:

```bash
sudo systemctl status animeattire.service
sudo systemctl reload animeattire.service
docker compose --env-file /etc/animeattire/production.env -f docker-compose.vps.yml logs -f
```

## Operational notes

- do not expose backend or frontend ports directly on the public interface;
- keep `APP_DOMAIN`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and
  `CORS_ALLOWED_ORIGINS` aligned;
- if media is routed to S3-compatible storage, `/media/*` becomes a fallback
  only and runtime uploads should use the configured object storage backend;
- database migrations currently run at container startup; the more advanced
  zero-downtime release strategy remains a separate later plan item.

## What stays open after this

This deployment target closes the current base infrastructure choice. These
follow-up items remain intentionally separate:

- zero-downtime migration/deploy strategy;
- rollback commands and release checklist;
- scheduled backup drill execution on staging;
- dedicated Celery beat deployment if periodic workloads become required.
