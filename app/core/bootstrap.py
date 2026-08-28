from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.models import Category, CategoryType, Profile, User, UserRole


SYSTEM_CATEGORIES = [
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


def seed_defaults() -> None:
    """Create idempotent system data after migrations have been applied."""
    db = SessionLocal()
    try:
        for name, category_type, icon, color in SYSTEM_CATEGORIES:
            exists = db.query(Category).filter_by(name=name, is_system=True).first()
            if not exists:
                db.add(Category(name=name, type=category_type, icon=icon, color=color, is_system=True))

        if settings.admin_password:
            admin = db.query(User).filter_by(email=settings.admin_email).first()
            if not admin:
                admin = User(
                    email=settings.admin_email.lower(),
                    name="Administrador",
                    password_hash=hash_password(settings.admin_password),
                    role=UserRole.admin,
                    is_active=True,
                )
                db.add(admin)
                db.flush()
                db.add(Profile(user_id=admin.id))
        db.commit()
    finally:
        db.close()
