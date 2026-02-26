#!/usr/bin/env bash
# Build script for Render deployment
set -o errexit

cd backend

pip install -r requirements.txt

python manage.py collectstatic --no-input || true
python manage.py migrate --run-syncdb || true
