"""Sincroniza dados padrão depois de `python scripts/migrate.py`."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.bootstrap import seed_defaults


if __name__ == "__main__":
    seed_defaults()
    print("Dados iniciais sincronizados.")
