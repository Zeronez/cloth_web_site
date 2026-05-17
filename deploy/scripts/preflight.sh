#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${ENV_FILE:-/etc/animeattire/production.env}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.vps.yml}"

cd "$ROOT_DIR"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config >/dev/null
docker run --rm \
  -e APP_DOMAIN="${APP_DOMAIN:?APP_DOMAIN must be set in $ENV_FILE}" \
  -e ACME_EMAIL="${ACME_EMAIL:?ACME_EMAIL must be set in $ENV_FILE}" \
  -v "$ROOT_DIR/deploy/caddy/Caddyfile:/etc/caddy/Caddyfile:ro" \
  caddy:2.10-alpine \
  caddy validate --config /etc/caddy/Caddyfile >/dev/null

echo "Deploy preflight checks passed."
