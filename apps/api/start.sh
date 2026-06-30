#!/usr/bin/env sh
# Production entrypoint: apply migrations, then serve.
# Railway/Render inject $PORT; default to 8000 locally.
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
