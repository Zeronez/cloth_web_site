#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <git-ref>" >&2
  exit 1
fi

TARGET_REF="$1"
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

git fetch --all --tags
git checkout "$TARGET_REF"

"${COMPOSE[@]}" config >/dev/null

echo "Rebuilding application services for rollback target $TARGET_REF..."
"${COMPOSE[@]}" up -d --build --no-deps "${SERVICES[@]}"

echo "Rollback deployment finished. Verify health before declaring success."
echo "If the release contained backward-incompatible migrations, perform the documented database rollback procedure separately."
