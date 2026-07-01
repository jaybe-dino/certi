#!/usr/bin/env sh
# Production entrypoint: wait for DB, apply migrations (with retry), then serve.
# Railway/Render inject $PORT; default to 8000 locally.
#
# The retry loop tolerates the brief delay before a managed database's
# private network / DNS becomes reachable right after a deploy.

echo "Applying database migrations..."
attempt=0
max_attempts=15
until alembic upgrade head; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge "$max_attempts" ]; then
    echo "ERROR: migrations failed after ${attempt} attempts; exiting."
    exit 1
  fi
  echo "Migration attempt ${attempt} failed (DB not ready?). Retrying in 3s..."
  sleep 3
done
echo "Migrations applied."

echo "Starting uvicorn on port ${PORT:-8000}..."
# Bind to IPv6 (dual-stack) so Railway's private/edge network (IPv6) can reach
# the app. A dual-stack :: socket also accepts IPv4 (e.g. localhost healthcheck).
exec uvicorn app.main:app --host :: --port "${PORT:-8000}"
