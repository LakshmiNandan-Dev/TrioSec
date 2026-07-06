#!/bin/sh
set -e

python -m app.wait_for_db
alembic upgrade head

exec "$@"
