#!/bin/sh
set -e

echo "Inicializando banco de dados..."
python scripts/seed.py

echo "Iniciando servidor..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
