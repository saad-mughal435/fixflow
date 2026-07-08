#!/usr/bin/env bash
# Render build step for the API: install deps, collect static, migrate, and
# seed demo data on first deploy (seed is idempotent — it only generates
# requests when the database is empty).
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

if [ "$DEMO_MODE" = "true" ]; then
  python manage.py seed
fi
