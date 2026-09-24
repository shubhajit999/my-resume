#!/bin/sh
set -e

echo "=== ResumeForge Container Startup ==="
echo "Executing database migrations (alembic upgrade head)..."
python -m alembic upgrade head

echo "Database migrations completed successfully."
echo "Launching Uvicorn web server..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
