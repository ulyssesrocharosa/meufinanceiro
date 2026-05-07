"""
Apaga apenas os dados financeiros, mantendo usuários, perfis e categorias do sistema.
Rodar: python scripts/clear_db.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine

confirm1 = input("⚠️  ATENÇÃO: isso apaga todos os dados financeiros permanentemente. Digite 'sim' para continuar: ").strip().lower()
if confirm1 != "sim":
    print("Cancelado.")
    sys.exit(0)

confirm2 = input("🔴 Tem CERTEZA? Esta ação não pode ser desfeita. Digite 'deletar' para confirmar: ").strip().lower()
if confirm2 != "deletar":
    print("Cancelado.")
    sys.exit(0)

# Ordem importa: tabelas filhas antes das pai (FK constraints)
TABLES = [
    "transaction_tags",
    "notifications",
    "investments",
    "debts",
    "goals",
    "budgets",
    "transactions",
    "recurring_bills",
    "tags",
    "accounts",
    # categorias do usuário (is_system=False) — mantém as do sistema
]

with engine.connect() as conn:
    for table in TABLES:
        conn.execute(text(f"DELETE FROM {table}"))
        print(f"  {table} limpa.")

    # Remove apenas categorias personalizadas, mantém as do sistema
    conn.execute(text("DELETE FROM categories WHERE is_system = 0"))
    print("  categories (personalizadas) limpas.")

    conn.commit()

print("\nDados financeiros apagados. Usuários, perfis e categorias do sistema preservados.")
