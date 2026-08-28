#!/bin/sh
set -eu

python scripts/migrate.py
python scripts/seed.py
exec "$@"
