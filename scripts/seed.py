"""
Seed: popula o banco com admin + categorias do sistema.
Rodar: python scripts/seed.py (de dentro de financeiropython/)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.core.database import SessionLocal, engine
from app.core.config import settings
from app.models.models import Base, User, Profile, Category, UserRole, CategoryType
from app.core.security import hash_password

SYSTEM_CATEGORIES = [
    # (name, type, icon, color)
    ("Salário", CategoryType.income, "briefcase", "#10B981"),
    ("Freelance", CategoryType.income, "code", "#3B82F6"),
    ("Rendimentos", CategoryType.income, "trending-up", "#8B5CF6"),
    ("Outros (receita)", CategoryType.income, "plus-circle", "#6B7280"),
    ("Alimentação", CategoryType.expense, "utensils", "#EF4444"),
    ("Transporte", CategoryType.expense, "car", "#F59E0B"),
    ("Saúde", CategoryType.expense, "heart", "#EC4899"),
    ("Educação", CategoryType.expense, "book", "#3B82F6"),
    ("Moradia", CategoryType.expense, "home", "#8B5CF6"),
    ("Lazer", CategoryType.expense, "smile", "#F97316"),
    ("Vestuário", CategoryType.expense, "shopping-bag", "#14B8A6"),
    ("Serviços", CategoryType.expense, "tool", "#6366F1"),
    ("Assinaturas", CategoryType.expense, "repeat", "#A855F7"),
    ("Outros (despesa)", CategoryType.expense, "minus-circle", "#6B7280"),
    ("Transferência", CategoryType.transfer, "arrow-left-right", "#94A3B8"),
]


def _migrate(conn) -> None:
    """Aplica colunas novas em tabelas já existentes (idempotente)."""
    migrations = [
        "ALTER TABLE profiles ADD COLUMN notif_bill_hour INTEGER DEFAULT 8",
        "ALTER TABLE profiles ADD COLUMN notif_budget_hour INTEGER DEFAULT 9",
    ]
    for sql in migrations:
        try:
            conn.execute(text(sql))
            conn.commit()
        except Exception:
            pass  # coluna já existe


def seed():
    print("Criando tabelas...")
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        _migrate(conn)

    db = SessionLocal()
    try:
        # Admin user
        existing = db.query(User).filter_by(email=settings.admin_email).first()
        if not existing:
            admin = User(
                email=settings.admin_email,
                name="Administrador",
                password_hash=hash_password(settings.admin_password),
                role=UserRole.admin,
                is_active=True,
            )
            db.add(admin)
            db.flush()
            db.add(Profile(user_id=admin.id))
            print(f"Admin criado: {settings.admin_email}")
        else:
            print(f"Admin já existe: {settings.admin_email}")

        # System categories
        created = 0
        for name, ctype, icon, color in SYSTEM_CATEGORIES:
            exists = db.query(Category).filter_by(name=name, is_system=True).first()
            if not exists:
                db.add(Category(
                    name=name, type=ctype, icon=icon, color=color,
                    is_system=True, user_id=None,
                ))
                created += 1

        db.commit()
        print(f"Categorias do sistema criadas: {created}")
        print("Seed concluído com sucesso!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
