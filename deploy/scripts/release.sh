#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${ENV_FILE:-/etc/animeattire/production.env}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.vps.yml}"
COMPOSE=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")
SERVICES=(backend frontend celery celery-beat caddy)

cd "$ROOT_DIR"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

"${COMPOSE[@]}" config >/dev/null

echo "Running Django migrations..."
echo "Checking migration safety policy..."
"${COMPOSE[@]}" run --rm backend python manage.py checkmigrationsafety

echo "Running Django migrations..."
"${COMPOSE[@]}" run --rm backend python manage.py migrate --noinput

echo "Collecting static assets..."
"${COMPOSE[@]}" run --rm backend python manage.py collectstatic --noinput

echo "Refreshing application services..."
"${COMPOSE[@]}" up -d --build --no-deps "${SERVICES[@]}"

echo "Waiting for backend health..."
for attempt in {1..30}; do
  if "${COMPOSE[@]}" exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/ready/', timeout=3).read()" >/dev/null 2>&1; then
    break
  fi
  if [[ "$attempt" -eq 30 ]]; then
    echo "Backend did not become ready in time." >&2
    exit 1
  fi
  sleep 2
done

echo "Waiting for frontend health..."
for attempt in {1..30}; do
  if "${COMPOSE[@]}" exec -T frontend node -e "fetch('http://127.0.0.1:3000').then((response) => { if (!response.ok) process.exit(1); }).catch(() => process.exit(1))" >/dev/null 2>&1; then
    break
  fi
  if [[ "$attempt" -eq 30 ]]; then
    echo "Frontend did not become ready in time." >&2
    exit 1
  fi
  sleep 2
done

echo "Release completed successfully."
