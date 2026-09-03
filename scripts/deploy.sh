#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/wakilidesk}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
WAKILIDESK_ENV_FILE="${WAKILIDESK_ENV_FILE:-.env.prod}"

cd "$APP_DIR"

if [ ! -f "$WAKILIDESK_ENV_FILE" ]; then
  echo "Missing $WAKILIDESK_ENV_FILE in $APP_DIR. Create it from .env.prod.example before deploying." >&2
  exit 1
fi

export WAKILIDESK_ENV_FILE

docker compose --env-file "$WAKILIDESK_ENV_FILE" -f "$COMPOSE_FILE" build
docker compose --env-file "$WAKILIDESK_ENV_FILE" -f "$COMPOSE_FILE" up -d db redis
docker compose --env-file "$WAKILIDESK_ENV_FILE" -f "$COMPOSE_FILE" run --rm web python manage.py migrate --noinput
docker compose --env-file "$WAKILIDESK_ENV_FILE" -f "$COMPOSE_FILE" run --rm web python manage.py collectstatic --noinput
docker compose --env-file "$WAKILIDESK_ENV_FILE" -f "$COMPOSE_FILE" up -d web worker
docker compose --env-file "$WAKILIDESK_ENV_FILE" -f "$COMPOSE_FILE" exec -T web python manage.py check

echo "wakiliDesk deployment complete."
