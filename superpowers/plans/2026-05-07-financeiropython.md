# Minhas Finanças Python — Plano de Implementação

> **Para agentes:** Use superpowers:executing-plans ou superpowers:subagent-driven-development para executar este plano.

**Goal:** Criar sistema financeiro pessoal completo em FastAPI + Jinja2 + SQLite na pasta `financeiropython/`

**Architecture:** Modular por recurso. Cada módulo tem router.py, service.py e templates/. Core compartilhado em app/core/. Um container Docker com Uvicorn.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, Jinja2, Tailwind CDN, Chart.js CDN, APScheduler, Evolution API (WhatsApp), SQLite3

---

## Fase 1 — Fundação

### Task 1: Scaffolding do projeto

**Files:**
- Create: `financeiropython/requirements.txt`
- Create: `financeiropython/.env.example`
- Create: `financeiropython/app/__init__.py`
- Create: `financeiropython/app/core/__init__.py`
- Create: `financeiropython/app/models/__init__.py`
- Create: todos os `__init__.py` dos módulos

- [ ] Criar estrutura de pastas:
```bash
cd "FINANCEIRO 27 de abril)"
mkdir -p financeiropython/app/core
mkdir -p financeiropython/app/models
mkdir -p financeiropython/app/modules/auth/templates
mkdir -p financeiropython/app/modules/dashboard/templates
mkdir -p financeiropython/app/modules/transactions/templates
mkdir -p financeiropython/app/modules/accounts/templates
mkdir -p financeiropython/app/modules/categories/templates
mkdir -p financeiropython/app/modules/recurring/templates
mkdir -p financeiropython/app/modules/budgets/templates
mkdir -p financeiropython/app/modules/goals/templates
mkdir -p financeiropython/app/modules/debts/templates
mkdir -p financeiropython/app/modules/investments/templates
mkdir -p financeiropython/app/modules/reports/templates
mkdir -p financeiropython/app/modules/notifications/templates
mkdir -p financeiropython/app/modules/whatsapp
mkdir -p financeiropython/app/modules/admin/templates
mkdir -p financeiropython/app/templates/shared
mkdir -p financeiropython/static
mkdir -p financeiropython/data
mkdir -p financeiropython/scripts
mkdir -p financeiropython/tests
```

- [ ] Criar `financeiropython/requirements.txt`:
```
fastapi==0.115.5
uvicorn[standard]==0.29.0
sqlalchemy==2.0.36
alembic==1.13.3
jinja2==3.1.4
python-multipart==0.0.12
itsdangerous==2.2.0
passlib[bcrypt]==1.7.4
httpx==0.27.2
apscheduler==3.10.4
pydantic-settings==2.6.1
python-dotenv==1.0.1
pytest==8.3.3
pytest-asyncio==0.24.0
httpx==0.27.2
```

- [ ] Criar `financeiropython/.env.example`:
```
SECRET_KEY=troque-por-string-aleatoria-longa
DATABASE_URL=sqlite:////app/data/financas.db
ADMIN_EMAIL=admin@minhasfinancas.com
ADMIN_PASSWORD=senha-segura-aqui
EVOLUTION_API_URL=https://evolution.seudominio.com
EVOLUTION_API_KEY=sua-chave-api
EVOLUTION_INSTANCE=nome-da-instancia
```

- [ ] Criar `financeiropython/.env` (cópia do .env.example com valores reais)

- [ ] Commit: `git add financeiropython/ && git commit -m "feat: scaffolding financeiropython"`

---

### Task 2: Config + Database

**Files:**
- Create: `financeiropython/app/core/config.py`
- Create: `financeiropython/app/core/database.py`

- [ ] Criar `app/core/config.py`:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    secret_key: str
    database_url: str = "sqlite:///./data/financas.db"
    admin_email: str = "admin@financas.com"
    admin_password: str = "admin123"
    evolution_api_url: str = ""
    evolution_api_key: str = ""
    evolution_instance: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
```

- [ ] Criar `app/core/database.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] Commit: `git commit -m "feat: core config e database"`

---

### Task 3: Modelos SQLAlchemy

**Files:**
- Create: `financeiropython/app/models/models.py`

- [ ] Criar `app/models/models.py` com todos os modelos:
```python
from datetime import datetime, date
from sqlalchemy import (
    Integer, String, Boolean, Float, Date, DateTime,
    ForeignKey, Text, Enum as SAEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional
import enum
from app.core.database import Base

class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"

class AccountType(str, enum.Enum):
    checking = "checking"
    savings = "savings"
    credit = "credit"
    investment = "investment"
    cash = "cash"
    other = "other"

class CategoryType(str, enum.Enum):
    income = "income"
    expense = "expense"
    transfer = "transfer"

class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"
    transfer = "transfer"

class TransactionStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    cancelled = "cancelled"

class RecurringFrequency(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"

class BudgetPeriod(str, enum.Enum):
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"

class GoalPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

class DebtType(str, enum.Enum):
    credit_card = "credit_card"
    loan = "loan"
    mortgage = "mortgage"
    personal = "personal"
    other = "other"

class DebtStatus(str, enum.Enum):
    active = "active"
    paid = "paid"
    defaulted = "defaulted"

class InvestmentType(str, enum.Enum):
    stock = "stock"
    bond = "bond"
    fund = "fund"
    crypto = "crypto"
    real_estate = "real_estate"
    other = "other"

class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

class NotificationType(str, enum.Enum):
    bill_reminder = "bill_reminder"
    budget_alert = "budget_alert"
    goal_update = "goal_update"
    system = "system"
    transaction = "transaction"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.user)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    profile: Mapped[Optional["Profile"]] = relationship(back_populates="user", uselist=False)
    accounts: Mapped[list["Account"]] = relationship(back_populates="user", cascade="all, delete")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user", cascade="all, delete")
    categories: Mapped[list["Category"]] = relationship(back_populates="user", cascade="all, delete")
    recurring_bills: Mapped[list["RecurringBill"]] = relationship(back_populates="user", cascade="all, delete")
    budgets: Mapped[list["Budget"]] = relationship(back_populates="user", cascade="all, delete")
    goals: Mapped[list["Goal"]] = relationship(back_populates="user", cascade="all, delete")
    tags: Mapped[list["Tag"]] = relationship(back_populates="user", cascade="all, delete")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user", cascade="all, delete")
    debts: Mapped[list["Debt"]] = relationship(back_populates="user", cascade="all, delete")
    investments: Mapped[list["Investment"]] = relationship(back_populates="user", cascade="all, delete")


class Profile(Base):
    __tablename__ = "profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    currency: Mapped[str] = mapped_column(String(3), default="BRL")
    timezone: Mapped[str] = mapped_column(String(50), default="America/Sao_Paulo")
    theme: Mapped[str] = mapped_column(String(10), default="light")
    whatsapp_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    whatsapp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    user: Mapped["User"] = relationship(back_populates="profile")


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[AccountType] = mapped_column(SAEnum(AccountType))
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(3), default="BRL")
    institution: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    account_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    color: Mapped[str] = mapped_column(String(7), default="#3B82F6")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped["User"] = relationship(back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")
    goals: Mapped[list["Goal"]] = relationship(back_populates="target_account")
    investments: Mapped[list["Investment"]] = relationship(back_populates="account")


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[CategoryType] = mapped_column(SAEnum(CategoryType))
    icon: Mapped[str] = mapped_column(String(50), default="dollar-sign")
    color: Mapped[str] = mapped_column(String(7), default="#6B7280")
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped[Optional["User"]] = relationship(back_populates="categories")
    parent: Mapped[Optional["Category"]] = relationship(remote_side="Category.id", back_populates="children")
    children: Mapped[list["Category"]] = relationship(back_populates="parent")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="category")
    budgets: Mapped[list["Budget"]] = relationship(back_populates="category")
    recurring_bills: Mapped[list["RecurringBill"]] = relationship(back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    recurring_bill_id: Mapped[Optional[int]] = mapped_column(ForeignKey("recurring_bills.id", ondelete="SET NULL"), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[TransactionType] = mapped_column(SAEnum(TransactionType))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(SAEnum(TransactionStatus), default=TransactionStatus.completed)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_reconciled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user: Mapped["User"] = relationship(back_populates="transactions")
    account: Mapped["Account"] = relationship(back_populates="transactions")
    category: Mapped[Optional["Category"]] = relationship(back_populates="transactions")
    recurring_bill: Mapped[Optional["RecurringBill"]] = relationship(back_populates="transactions")
    tags: Mapped[list["Tag"]] = relationship(secondary="transaction_tags", back_populates="transactions")


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str] = mapped_column(String(7), default="#6B7280")
    user: Mapped["User"] = relationship(back_populates="tags")
    transactions: Mapped[list["Transaction"]] = relationship(secondary="transaction_tags", back_populates="tags")


from sqlalchemy import Table, Column
transaction_tags = Table(
    "transaction_tags", Base.metadata,
    Column("transaction_id", ForeignKey("transactions.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class RecurringBill(Base):
    __tablename__ = "recurring_bills"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    frequency: Mapped[RecurringFrequency] = mapped_column(SAEnum(RecurringFrequency))
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    next_occurrence: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    days_before_reminder: Mapped[int] = mapped_column(Integer, default=3)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped["User"] = relationship(back_populates="recurring_bills")
    category: Mapped[Optional["Category"]] = relationship(back_populates="recurring_bills")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="recurring_bill")


class Budget(Base):
    __tablename__ = "budgets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    period: Mapped[BudgetPeriod] = mapped_column(SAEnum(BudgetPeriod))
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped["User"] = relationship(back_populates="budgets")
    category: Mapped["Category"] = relationship(back_populates="budgets")


class Goal(Base):
    __tablename__ = "goals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    target_amount: Mapped[float] = mapped_column(Float, nullable=False)
    current_amount: Mapped[float] = mapped_column(Float, default=0.0)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    priority: Mapped[GoalPriority] = mapped_column(SAEnum(GoalPriority), default=GoalPriority.medium)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user: Mapped["User"] = relationship(back_populates="goals")
    target_account: Mapped[Optional["Account"]] = relationship(back_populates="goals")


class Debt(Base):
    __tablename__ = "debts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    original_amount: Mapped[float] = mapped_column(Float, nullable=False)
    current_amount: Mapped[float] = mapped_column(Float, nullable=False)
    interest_rate: Mapped[float] = mapped_column(Float, default=0.0)
    type: Mapped[Optional[DebtType]] = mapped_column(SAEnum(DebtType), nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[DebtStatus] = mapped_column(SAEnum(DebtStatus), default=DebtStatus.active)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped["User"] = relationship(back_populates="debts")


class Investment(Base):
    __tablename__ = "investments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[Optional[InvestmentType]] = mapped_column(SAEnum(InvestmentType), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    current_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    risk_level: Mapped[Optional[RiskLevel]] = mapped_column(SAEnum(RiskLevel), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user: Mapped["User"] = relationship(back_populates="investments")
    account: Mapped["Account"] = relationship(back_populates="investments")


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[NotificationType] = mapped_column(SAEnum(NotificationType))
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped["User"] = relationship(back_populates="notifications")
```

- [ ] Commit: `git commit -m "feat: modelos SQLAlchemy completos"`

---

### Task 4: Alembic + migração inicial

**Files:**
- Create: `financeiropython/alembic.ini`
- Create: `financeiropython/alembic/env.py`

- [ ] Dentro de `financeiropython/`, inicializar Alembic:
```bash
cd financeiropython
alembic init alembic
```

- [ ] Editar `alembic/env.py` — substituir as linhas de target_metadata:
```python
from app.core.config import settings
from app.core.database import Base
from app.models.models import *  # importa todos os modelos

config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata
```

- [ ] Gerar migração inicial:
```bash
alembic revision --autogenerate -m "initial_schema"
alembic upgrade head
```

- [ ] Commit: `git commit -m "feat: alembic schema inicial"`

---

### Task 5: Seed (admin + categorias do sistema)

**Files:**
- Create: `financeiropython/scripts/seed.py`

- [ ] Criar `scripts/seed.py`:
```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import SessionLocal, engine
from app.core.config import settings
from app.models.models import Base, User, Profile, Category, UserRole, CategoryType
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SYSTEM_CATEGORIES = [
    # (name, type, icon, color)
    ("Salário", CategoryType.income, "briefcase", "#10B981"),
    ("Freelance", CategoryType.income, "code", "#3B82F6"),
    ("Investimentos", CategoryType.income, "trending-up", "#8B5CF6"),
    ("Outros (receita)", CategoryType.income, "plus-circle", "#6B7280"),
    ("Alimentação", CategoryType.expense, "utensils", "#EF4444"),
    ("Transporte", CategoryType.expense, "car", "#F59E0B"),
    ("Saúde", CategoryType.expense, "heart", "#EC4899"),
    ("Educação", CategoryType.expense, "book", "#3B82F6"),
    ("Moradia", CategoryType.expense, "home", "#8B5CF6"),
    ("Lazer", CategoryType.expense, "smile", "#F97316"),
    ("Vestuário", CategoryType.expense, "shopping-bag", "#14B8A6"),
    ("Serviços", CategoryType.expense, "tool", "#6366F1"),
    ("Outros (despesa)", CategoryType.expense, "minus-circle", "#6B7280"),
    ("Transferência", CategoryType.transfer, "repeat", "#94A3B8"),
]

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Admin user
        existing = db.query(User).filter_by(email=settings.admin_email).first()
        if not existing:
            admin = User(
                email=settings.admin_email,
                name="Administrador",
                password_hash=pwd_context.hash(settings.admin_password),
                role=UserRole.admin,
                is_active=True,
            )
            db.add(admin)
            db.flush()
            db.add(Profile(user_id=admin.id))

        # System categories
        for name, ctype, icon, color in SYSTEM_CATEGORIES:
            exists = db.query(Category).filter_by(name=name, is_system=True).first()
            if not exists:
                db.add(Category(name=name, type=ctype, icon=icon, color=color, is_system=True))

        db.commit()
        print("Seed concluído.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
```

- [ ] Rodar seed: `python scripts/seed.py`
- [ ] Commit: `git commit -m "feat: seed admin e categorias do sistema"`

---

## Fase 2 — Auth + Templates base

### Task 6: Template base (layout)

**Files:**
- Create: `financeiropython/app/templates/base.html`
- Create: `financeiropython/app/templates/shared/flash.html`
- Create: `financeiropython/static/app.js`

- [ ] Criar `app/templates/base.html` com:
  - `<head>` com Tailwind CDN, Chart.js CDN, Lucide CDN
  - Sidebar fixa à esquerda com links para todos os módulos
  - Navbar superior com nome do usuário, sino de notificações, logout
  - Bloco `{% block content %}` para páginas
  - Bloco `{% block scripts %}` para JS específico de página
  - Flash messages (sucesso/erro) no topo do content
  - Tema escuro/claro via classe no `<html>`

```html
<!DOCTYPE html>
<html lang="pt-BR" class="{{ 'dark' if user.profile and user.profile.theme == 'dark' else '' }}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Minhas Finanças{% endblock %}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>tailwind.config = { darkMode: 'class' }</script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
</head>
<body class="bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 flex h-screen overflow-hidden">

  <!-- Sidebar -->
  <aside class="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
    <div class="p-6 border-b border-gray-200 dark:border-gray-700">
      <h1 class="text-xl font-bold text-indigo-600">💰 Minhas Finanças</h1>
    </div>
    <nav class="flex-1 p-4 space-y-1 overflow-y-auto">
      {% set nav = [
        ("/", "home", "Dashboard"),
        ("/transactions", "arrow-left-right", "Transações"),
        ("/accounts", "wallet", "Contas"),
        ("/categories", "tag", "Categorias"),
        ("/recurring", "repeat", "Recorrentes"),
        ("/budgets", "pie-chart", "Orçamentos"),
        ("/goals", "target", "Metas"),
        ("/debts", "credit-card", "Dívidas"),
        ("/investments", "trending-up", "Investimentos"),
        ("/reports", "bar-chart-2", "Relatórios"),
        ("/notifications", "bell", "Notificações"),
      ] %}
      {% for href, icon, label in nav %}
      <a href="{{ href }}" class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium
         {{ 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300' if request.url.path == href
            else 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700' }}">
        <i data-lucide="{{ icon }}" class="w-4 h-4"></i>{{ label }}
        {% if label == "Notificações" and unread_count > 0 %}
        <span class="ml-auto bg-red-500 text-white text-xs rounded-full px-1.5">{{ unread_count }}</span>
        {% endif %}
      </a>
      {% endfor %}
      {% if user.role == 'admin' %}
      <a href="/admin" class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100">
        <i data-lucide="shield" class="w-4 h-4"></i>Admin
      </a>
      {% endif %}
    </nav>
    <div class="p-4 border-t border-gray-200 dark:border-gray-700">
      <a href="/auth/logout" class="flex items-center gap-2 text-sm text-gray-500 hover:text-red-500">
        <i data-lucide="log-out" class="w-4 h-4"></i>Sair
      </a>
    </div>
  </aside>

  <!-- Main -->
  <div class="flex-1 flex flex-col overflow-hidden">
    <!-- Topbar -->
    <header class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
      <h2 class="text-lg font-semibold">{% block page_title %}{% endblock %}</h2>
      <span class="text-sm text-gray-500">Olá, {{ user.name }}</span>
    </header>

    <!-- Flash messages -->
    {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
    <div class="px-6 pt-4 space-y-2">
      {% for category, message in messages %}
      <div class="px-4 py-3 rounded-lg text-sm font-medium
        {{ 'bg-green-50 text-green-800 border border-green-200' if category == 'success'
           else 'bg-red-50 text-red-800 border border-red-200' }}">
        {{ message }}
      </div>
      {% endfor %}
    </div>
    {% endif %}
    {% endwith %}

    <!-- Content -->
    <main class="flex-1 overflow-y-auto p-6">
      {% block content %}{% endblock %}
    </main>
  </div>

  <script>lucide.createIcons();</script>
  {% block scripts %}{% endblock %}
</body>
</html>
```

- [ ] Criar `static/app.js`:
```javascript
function confirmDelete(message) {
  return confirm(message || 'Confirmar exclusão?');
}
function toggleTheme() {
  document.documentElement.classList.toggle('dark');
  fetch('/profile/theme', { method: 'POST' });
}
```

- [ ] Commit: `git commit -m "feat: template base com sidebar e Tailwind"`

---

### Task 7: Auth module

**Files:**
- Create: `financeiropython/app/core/auth.py`
- Create: `financeiropython/app/modules/auth/router.py`
- Create: `financeiropython/app/modules/auth/templates/login.html`

- [ ] Criar `app/core/auth.py`:
```python
from fastapi import Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=302, headers={"Location": "/auth/login"})
    user = db.query(User).filter_by(id=user_id, is_active=True).first()
    if not user:
        request.session.clear()
        raise HTTPException(status_code=302, headers={"Location": "/auth/login"})
    return user

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    return user
```

- [ ] Criar `app/modules/auth/router.py`:
```python
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime
from app.core.database import get_db
from app.models.models import User

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=email, is_active=True).first()
    if not user or not pwd_context.verify(password, user.password_hash):
        return templates.TemplateResponse("auth/login.html", {
            "request": request, "error": "Email ou senha inválidos"
        }, status_code=400)
    user.last_login = datetime.utcnow()
    db.commit()
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=302)

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/auth/login", status_code=302)
```

- [ ] Criar `app/modules/auth/templates/login.html`:
```html
<!DOCTYPE html>
<html lang="pt-BR" class="">
<head>
  <meta charset="UTF-8">
  <title>Login — Minhas Finanças</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-indigo-50 to-blue-100 min-h-screen flex items-center justify-center">
  <div class="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
    <div class="text-center mb-8">
      <div class="text-4xl mb-2">💰</div>
      <h1 class="text-2xl font-bold text-gray-900">Minhas Finanças</h1>
      <p class="text-gray-500 text-sm mt-1">Acesse sua conta</p>
    </div>
    {% if error %}
    <div class="mb-4 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{{ error }}</div>
    {% endif %}
    <form method="POST" action="/auth/login" class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
        <input type="email" name="email" required autocomplete="email"
          class="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none">
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Senha</label>
        <input type="password" name="password" required autocomplete="current-password"
          class="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none">
      </div>
      <button type="submit"
        class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2.5 rounded-lg text-sm transition-colors">
        Entrar
      </button>
    </form>
  </div>
</body>
</html>
```

- [ ] Commit: `git commit -m "feat: auth login/logout com session cookie"`

---

### Task 8: main.py (app principal)

**Files:**
- Create: `financeiropython/app/main.py`

- [ ] Criar `app/main.py`:
```python
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User, Notification

# Routers
from app.modules.auth.router import router as auth_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.transactions.router import router as transactions_router
from app.modules.accounts.router import router as accounts_router
from app.modules.categories.router import router as categories_router
from app.modules.recurring.router import router as recurring_router
from app.modules.budgets.router import router as budgets_router
from app.modules.goals.router import router as goals_router
from app.modules.debts.router import router as debts_router
from app.modules.investments.router import router as investments_router
from app.modules.reports.router import router as reports_router
from app.modules.notifications.router import router as notifications_router
from app.modules.admin.router import router as admin_router

app = FastAPI(title="Minhas Finanças")
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="app/templates")

# Helper: injeta user e unread_count em todos os templates
def common_context(request: Request, user: User, db: Session):
    unread = db.query(Notification).filter_by(user_id=user.id, is_read=False).count()
    return {"request": request, "user": user, "unread_count": unread}

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(transactions_router)
app.include_router(accounts_router)
app.include_router(categories_router)
app.include_router(recurring_router)
app.include_router(budgets_router)
app.include_router(goals_router)
app.include_router(debts_router)
app.include_router(investments_router)
app.include_router(reports_router)
app.include_router(notifications_router)
app.include_router(admin_router)

@app.exception_handler(302)
async def redirect_handler(request, exc):
    return RedirectResponse(exc.headers["Location"])

@app.on_event("startup")
async def startup():
    from app.core.scheduler import start_scheduler
    start_scheduler()
```

- [ ] Commit: `git commit -m "feat: main.py com todos os routers registrados"`

---

## Fase 3 — Dashboard

### Task 9: Dashboard

**Files:**
- Create: `financeiropython/app/modules/dashboard/router.py`
- Create: `financeiropython/app/modules/dashboard/service.py`
- Create: `financeiropython/app/modules/dashboard/templates/dashboard.html`

- [ ] Criar `app/modules/dashboard/service.py`:
```python
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.models import Transaction, TransactionType, Account, Budget, RecurringBill

def get_dashboard_data(user_id: int, db: Session) -> dict:
    today = date.today()
    first_day = today.replace(day=1)

    income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.income,
        Transaction.date >= first_day,
        Transaction.date <= today,
    ).scalar() or 0.0

    expense = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.expense,
        Transaction.date >= first_day,
        Transaction.date <= today,
    ).scalar() or 0.0

    total_balance = db.query(func.sum(Account.balance)).filter(
        Account.user_id == user_id, Account.is_active == True
    ).scalar() or 0.0

    recent_transactions = db.query(Transaction).filter_by(user_id=user_id)\
        .order_by(Transaction.date.desc()).limit(10).all()

    upcoming_bills = db.query(RecurringBill).filter(
        RecurringBill.user_id == user_id,
        RecurringBill.is_active == True,
        RecurringBill.next_occurrence <= today + timedelta(days=7),
    ).all()

    # Últimos 6 meses para gráfico de linha
    months_data = []
    for i in range(5, -1, -1):
        ref = (today.replace(day=1) - timedelta(days=i * 30))
        m_start = ref.replace(day=1)
        m_end = (m_start.replace(month=m_start.month % 12 + 1, day=1) - timedelta(days=1)) \
                if m_start.month < 12 else m_start.replace(month=12, day=31)
        inc = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.income,
            Transaction.date >= m_start, Transaction.date <= m_end,
        ).scalar() or 0.0
        exp = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.expense,
            Transaction.date >= m_start, Transaction.date <= m_end,
        ).scalar() or 0.0
        months_data.append({"month": m_start.strftime("%b/%y"), "income": inc, "expense": exp})

    return {
        "total_balance": total_balance,
        "month_income": income,
        "month_expense": expense,
        "net": income - expense,
        "recent_transactions": recent_transactions,
        "upcoming_bills": upcoming_bills,
        "months_data": months_data,
    }
```

- [ ] Criar `app/modules/dashboard/router.py`:
```python
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User, Notification
from .service import get_dashboard_data

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = get_dashboard_data(user.id, db)
    unread = db.query(Notification).filter_by(user_id=user.id, is_read=False).count()
    return templates.TemplateResponse("dashboard/dashboard.html", {
        "request": request, "user": user, "unread_count": unread, **data
    })
```

- [ ] Criar `app/modules/dashboard/templates/dashboard.html` estendendo `base.html`:
  - 4 KPI cards: Saldo Total, Receitas do mês, Despesas do mês, Saldo líquido
  - Gráfico de linha (últimos 6 meses) via Chart.js
  - Tabela das últimas 10 transações
  - Lista de contas a vencer em 7 dias

- [ ] Commit: `git commit -m "feat: dashboard com KPIs e gráficos"`

---

## Fase 4 — Módulos financeiros core

### Task 10: Contas (Accounts)

**Files:**
- Create: `financeiropython/app/modules/accounts/router.py`
- Create: `financeiropython/app/modules/accounts/templates/list.html`
- Create: `financeiropython/app/modules/accounts/templates/form.html`

- [ ] Criar `app/modules/accounts/router.py` com rotas:
  - `GET /accounts` — lista todas as contas do usuário
  - `GET /accounts/new` — formulário de criação
  - `POST /accounts` — salvar nova conta (atualiza balance inicial)
  - `GET /accounts/{id}/edit` — formulário de edição
  - `POST /accounts/{id}` — salvar edição
  - `POST /accounts/{id}/delete` — desativar conta (soft delete: is_active=False)
  - `GET /accounts/{id}/transfer` — formulário de transferência entre contas
  - `POST /accounts/{id}/transfer` — salvar transferência (cria 2 transactions)

```python
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User, Account, AccountType, Transaction, TransactionType, TransactionStatus, Notification
from datetime import date

router = APIRouter(prefix="/accounts", tags=["accounts"])
templates = Jinja2Templates(directory="app/templates")

def _ctx(request, user, db):
    unread = db.query(Notification).filter_by(user_id=user.id, is_read=False).count()
    return {"request": request, "user": user, "unread_count": unread}

@router.get("", response_class=HTMLResponse)
def list_accounts(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    accounts = db.query(Account).filter_by(user_id=user.id).order_by(Account.name).all()
    return templates.TemplateResponse("accounts/list.html", {**_ctx(request, user, db), "accounts": accounts})

@router.get("/new", response_class=HTMLResponse)
def new_account_form(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return templates.TemplateResponse("accounts/form.html", {**_ctx(request, user, db), "account": None, "account_types": [t.value for t in AccountType]})

@router.post("")
def create_account(
    request: Request, name: str = Form(...), type: str = Form(...),
    balance: float = Form(0.0), institution: Optional[str] = Form(None),
    color: str = Form("#3B82F6"),
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    account = Account(user_id=user.id, name=name, type=AccountType(type), balance=balance, institution=institution, color=color)
    db.add(account)
    db.commit()
    return RedirectResponse("/accounts", status_code=302)

@router.get("/{id}/edit", response_class=HTMLResponse)
def edit_account_form(id: int, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = db.query(Account).filter_by(id=id, user_id=user.id).first()
    if not account:
        return RedirectResponse("/accounts", status_code=302)
    return templates.TemplateResponse("accounts/form.html", {**_ctx(request, user, db), "account": account, "account_types": [t.value for t in AccountType]})

@router.post("/{id}")
def update_account(
    id: int, name: str = Form(...), type: str = Form(...),
    institution: Optional[str] = Form(None), color: str = Form("#3B82F6"),
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    account = db.query(Account).filter_by(id=id, user_id=user.id).first()
    if account:
        account.name, account.type, account.institution, account.color = name, AccountType(type), institution, color
        db.commit()
    return RedirectResponse("/accounts", status_code=302)

@router.post("/{id}/delete")
def delete_account(id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = db.query(Account).filter_by(id=id, user_id=user.id).first()
    if account:
        account.is_active = False
        db.commit()
    return RedirectResponse("/accounts", status_code=302)

@router.post("/{id}/transfer")
def transfer(
    id: int, to_account_id: int = Form(...), amount: float = Form(...),
    description: Optional[str] = Form(None), transfer_date: str = Form(...),
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    from_acc = db.query(Account).filter_by(id=id, user_id=user.id).first()
    to_acc = db.query(Account).filter_by(id=to_account_id, user_id=user.id).first()
    if from_acc and to_acc:
        d = date.fromisoformat(transfer_date)
        db.add(Transaction(user_id=user.id, account_id=from_acc.id, amount=amount, type=TransactionType.transfer,
                           description=description or f"Transferência para {to_acc.name}", date=d, status=TransactionStatus.completed))
        db.add(Transaction(user_id=user.id, account_id=to_acc.id, amount=amount, type=TransactionType.transfer,
                           description=description or f"Transferência de {from_acc.name}", date=d, status=TransactionStatus.completed))
        from_acc.balance -= amount
        to_acc.balance += amount
        db.commit()
    return RedirectResponse("/accounts", status_code=302)
```

- [ ] Criar templates `accounts/list.html` e `accounts/form.html` estendendo `base.html`
- [ ] Commit: `git commit -m "feat: módulo contas (CRUD + transferência)"`

---

### Task 11: Categorias

**Files:**
- Create: `financeiropython/app/modules/categories/router.py`
- Create: `financeiropython/app/modules/categories/templates/list.html`
- Create: `financeiropython/app/modules/categories/templates/form.html`

- [ ] CRUD de categorias: `GET/POST /categories`, `GET /categories/new`, `GET/POST /categories/{id}/edit`, `POST /categories/{id}/delete`
  - Não permitir deletar categorias do sistema (`is_system=True`)
  - Listar separado: categorias do sistema + categorias do usuário
- [ ] Commit: `git commit -m "feat: módulo categorias"`

---

### Task 12: Transações

**Files:**
- Create: `financeiropython/app/modules/transactions/router.py`
- Create: `financeiropython/app/modules/transactions/service.py`
- Create: `financeiropython/app/modules/transactions/templates/list.html`
- Create: `financeiropython/app/modules/transactions/templates/form.html`

- [ ] Criar `app/modules/transactions/service.py`:
```python
from sqlalchemy.orm import Session
from app.models.models import Account, Transaction, TransactionType

def apply_transaction_to_balance(account: Account, amount: float, ttype: TransactionType, reverse: bool = False):
    """Atualiza saldo da conta conforme tipo da transação."""
    factor = -1 if reverse else 1
    if ttype == TransactionType.income:
        account.balance += amount * factor
    elif ttype == TransactionType.expense:
        account.balance -= amount * factor
```

- [ ] Criar `app/modules/transactions/router.py` com:
  - `GET /transactions` — lista com filtros (mês, tipo, conta, categoria, busca)
  - `GET /transactions/new` — formulário
  - `POST /transactions` — salvar + atualizar saldo da conta
  - `GET /transactions/{id}/edit` — formulário de edição
  - `POST /transactions/{id}` — salvar edição (reverter saldo antigo, aplicar novo)
  - `POST /transactions/{id}/delete` — deletar + reverter saldo

- [ ] Commit: `git commit -m "feat: módulo transações com filtros e atualização de saldo"`

---

### Task 13: Contas Recorrentes

**Files:**
- Create: `financeiropython/app/modules/recurring/router.py`
- Create: `financeiropython/app/modules/recurring/service.py`
- Create: `financeiropython/app/modules/recurring/templates/list.html`
- Create: `financeiropython/app/modules/recurring/templates/form.html`

- [ ] Criar `app/modules/recurring/service.py`:
```python
from datetime import date
from dateutil.relativedelta import relativedelta
from app.models.models import RecurringFrequency

def calc_next_occurrence(current: date, frequency: RecurringFrequency) -> date:
    if frequency == RecurringFrequency.daily:
        return current + relativedelta(days=1)
    elif frequency == RecurringFrequency.weekly:
        return current + relativedelta(weeks=1)
    elif frequency == RecurringFrequency.monthly:
        return current + relativedelta(months=1)
    elif frequency == RecurringFrequency.quarterly:
        return current + relativedelta(months=3)
    elif frequency == RecurringFrequency.yearly:
        return current + relativedelta(years=1)
```

- [ ] Adicionar `python-dateutil` em `requirements.txt`
- [ ] CRUD de recorrentes + botão "Registrar pagamento" (cria Transaction e avança next_occurrence)
- [ ] Commit: `git commit -m "feat: módulo contas recorrentes"`

---

## Fase 5 — Módulos de planejamento

### Task 14: Orçamentos

**Files:**
- Create: `financeiropython/app/modules/budgets/router.py`
- Create: `financeiropython/app/modules/budgets/templates/list.html`
- Create: `financeiropython/app/modules/budgets/templates/form.html`

- [ ] CRUD de orçamentos com `spent` calculado on-the-fly via query SUM
- [ ] Barra de progresso colorida: verde < 70%, amarelo 70-90%, vermelho > 90%
- [ ] Commit: `git commit -m "feat: módulo orçamentos"`

---

### Task 15: Metas

**Files:**
- Create: `financeiropython/app/modules/goals/router.py`
- Create: `financeiropython/app/modules/goals/templates/list.html`
- Create: `financeiropython/app/modules/goals/templates/form.html`

- [ ] CRUD de metas com barra de progresso e dias restantes calculados
- [ ] Commit: `git commit -m "feat: módulo metas"`

---

### Task 16: Dívidas

**Files:**
- Create: `financeiropython/app/modules/debts/router.py`
- Create: `financeiropython/app/modules/debts/templates/list.html`
- Create: `financeiropython/app/modules/debts/templates/form.html`

- [ ] CRUD de dívidas com % paga calculada (original - current / original)
- [ ] Commit: `git commit -m "feat: módulo dívidas"`

---

### Task 17: Investimentos

**Files:**
- Create: `financeiropython/app/modules/investments/router.py`
- Create: `financeiropython/app/modules/investments/templates/list.html`
- Create: `financeiropython/app/modules/investments/templates/form.html`

- [ ] CRUD de investimentos com rentabilidade calculada ((current_value - amount) / amount * 100)
- [ ] Commit: `git commit -m "feat: módulo investimentos"`

---

## Fase 6 — Relatórios + Notificações

### Task 18: Relatórios

**Files:**
- Create: `financeiropython/app/modules/reports/router.py`
- Create: `financeiropython/app/modules/reports/service.py`
- Create: `financeiropython/app/modules/reports/templates/index.html`

- [ ] Criar `app/modules/reports/service.py` com 4 tipos de relatório gerados on-the-fly:
  - `monthly_summary(user_id, month, year, db)` — receitas x despesas do mês
  - `spending_by_category(user_id, start, end, db)` — gasto por categoria (gráfico pizza)
  - `income_vs_expense(user_id, months, db)` — comparativo 6/12 meses (gráfico barras)
  - `net_worth(user_id, db)` — saldo total contas + investimentos - dívidas

- [ ] `GET /reports` — página com seletor de tipo e período, exibe resultado
- [ ] Commit: `git commit -m "feat: módulo relatórios on-the-fly"`

---

### Task 19: Notificações

**Files:**
- Create: `financeiropython/app/modules/notifications/router.py`
- Create: `financeiropython/app/modules/notifications/templates/index.html`

- [ ] `GET /notifications` — lista todas (não lidas primeiro)
- [ ] `POST /notifications/{id}/read` — marcar como lida
- [ ] `POST /notifications/read-all` — marcar todas como lidas
- [ ] Commit: `git commit -m "feat: módulo notificações"`

---

## Fase 7 — Admin

### Task 20: Painel Admin

**Files:**
- Create: `financeiropython/app/modules/admin/router.py`
- Create: `financeiropython/app/modules/admin/templates/index.html`
- Create: `financeiropython/app/modules/admin/templates/user_form.html`

- [ ] Criar `app/modules/admin/router.py`:
  - `GET /admin` — lista usuários (requer `require_admin`)
  - `GET /admin/users/new` — formulário novo usuário
  - `POST /admin/users` — criar usuário (hash da senha, cria Profile)
  - `POST /admin/users/{id}/toggle` — ativar/desativar
  - `POST /admin/users/{id}/reset-password` — resetar senha (nova senha no form)
- [ ] Commit: `git commit -m "feat: painel admin (gestão de usuários)"`

---

## Fase 8 — WhatsApp + Scheduler

### Task 21: WhatsApp service

**Files:**
- Create: `financeiropython/app/modules/whatsapp/service.py`

- [ ] Criar `app/modules/whatsapp/service.py`:
```python
import httpx
from app.core.config import settings

async def send_whatsapp(phone: str, message: str) -> bool:
    if not settings.evolution_api_url or not phone:
        return False
    url = f"{settings.evolution_api_url}/message/sendText/{settings.evolution_instance}"
    headers = {"apikey": settings.evolution_api_key, "Content-Type": "application/json"}
    payload = {"number": phone, "text": message}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, json=payload, headers=headers)
            return r.status_code == 200
    except Exception:
        return False
```

- [ ] Commit: `git commit -m "feat: WhatsApp service via Evolution API"`

---

### Task 22: Scheduler (APScheduler)

**Files:**
- Create: `financeiropython/app/core/scheduler.py`

- [ ] Criar `app/core/scheduler.py`:
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date, timedelta
import asyncio
from app.core.database import SessionLocal
from app.models.models import RecurringBill, Budget, Goal, User, Notification, NotificationType, Transaction, TransactionType
from sqlalchemy import func

scheduler = BackgroundScheduler()

def _get_db():
    db = SessionLocal()
    try:
        return db
    except:
        db.close()
        raise

def check_bill_reminders():
    db = SessionLocal()
    try:
        today = date.today()
        bills = db.query(RecurringBill).filter(
            RecurringBill.is_active == True,
            RecurringBill.next_occurrence <= today + timedelta(days=7),
        ).all()
        for bill in bills:
            user = db.query(User).filter_by(id=bill.user_id).first()
            days_left = (bill.next_occurrence - today).days
            msg = f"⚠️ Lembrete: *{bill.name}* vence em {days_left} dia(s) — R$ {bill.amount:.2f}"
            db.add(Notification(
                user_id=user.id, type=NotificationType.bill_reminder,
                title=f"Conta a vencer: {bill.name}", message=msg
            ))
            if user.profile and user.profile.whatsapp_enabled and user.profile.whatsapp_phone:
                asyncio.run(_send_wp(user.profile.whatsapp_phone, msg))
        db.commit()
    finally:
        db.close()

def check_budget_alerts():
    db = SessionLocal()
    try:
        today = date.today()
        budgets = db.query(Budget).filter(
            Budget.start_date <= today, Budget.end_date >= today
        ).all()
        for budget in budgets:
            spent = db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == budget.user_id,
                Transaction.category_id == budget.category_id,
                Transaction.type == TransactionType.expense,
                Transaction.date >= budget.start_date,
                Transaction.date <= budget.end_date,
            ).scalar() or 0.0
            pct = (spent / budget.amount * 100) if budget.amount > 0 else 0
            if pct >= 80:
                user = db.query(User).filter_by(id=budget.user_id).first()
                msg = f"🔴 Orçamento *{budget.category.name}*: {pct:.0f}% utilizado (R$ {spent:.2f} / R$ {budget.amount:.2f})"
                db.add(Notification(
                    user_id=user.id, type=NotificationType.budget_alert,
                    title=f"Alerta de orçamento: {budget.category.name}", message=msg
                ))
                if user.profile and user.profile.whatsapp_enabled and user.profile.whatsapp_phone:
                    asyncio.run(_send_wp(user.profile.whatsapp_phone, msg))
        db.commit()
    finally:
        db.close()

async def _send_wp(phone, msg):
    from app.modules.whatsapp.service import send_whatsapp
    await send_whatsapp(phone, msg)

def start_scheduler():
    scheduler.add_job(check_bill_reminders, CronTrigger(hour=8, minute=0))
    scheduler.add_job(check_budget_alerts, CronTrigger(hour=9, minute=0))
    scheduler.start()
```

- [ ] Commit: `git commit -m "feat: scheduler APScheduler (bill reminders + budget alerts)"`

---

## Fase 9 — Docker + Deploy

### Task 23: Docker

**Files:**
- Create: `financeiropython/Dockerfile`
- Create: `financeiropython/docker-compose.yml`
- Create: `financeiropython/docker-stack.yml`

- [ ] Criar `financeiropython/Dockerfile`:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/data
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] Criar `financeiropython/docker-compose.yml` (dev local):
```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - ./data:/app/data
    env_file: .env
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- [ ] Criar `financeiropython/docker-stack.yml` (Swarm + Traefik):
```yaml
version: "3.8"
services:
  financeiropython:
    image: ${REGISTRY}/financeiropython:${TAG:-latest}
    volumes:
      - financas_data:/app/data
    environment:
      DATABASE_URL: sqlite:////app/data/financas.db
      SECRET_KEY: ${SECRET_KEY}
      ADMIN_EMAIL: ${ADMIN_EMAIL}
      ADMIN_PASSWORD: ${ADMIN_PASSWORD}
      EVOLUTION_API_URL: ${EVOLUTION_API_URL}
      EVOLUTION_API_KEY: ${EVOLUTION_API_KEY}
      EVOLUTION_INSTANCE: ${EVOLUTION_INSTANCE}
    deploy:
      replicas: 1
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.financas-py.rule=Host(`financas.${DOMAIN}`)"
        - "traefik.http.routers.financas-py.entrypoints=websecure"
        - "traefik.http.routers.financas-py.tls.certresolver=letsencrypt"
        - "traefik.http.services.financas-py.loadbalancer.server.port=8000"
    networks:
      - traefik-public

volumes:
  financas_data:

networks:
  traefik-public:
    external: true
```

- [ ] Adicionar `.dockerignore`:
```
__pycache__/
*.pyc
.env
data/
.git/
```

- [ ] Commit: `git commit -m "feat: Docker + Swarm + Traefik config"`

---

## Testes base

### Task 24: Setup de testes

**Files:**
- Create: `financeiropython/tests/conftest.py`
- Create: `financeiropython/tests/test_auth.py`

- [ ] Criar `tests/conftest.py`:
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.main import app

SQLALCHEMY_TEST_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

- [ ] Criar `tests/test_auth.py`:
```python
from passlib.context import CryptContext
from app.models.models import User, UserRole, Profile

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_test_user(db, email="test@test.com", password="test123", role=UserRole.user):
    user = User(email=email, name="Test User", password_hash=pwd_context.hash(password), role=role, is_active=True)
    db.add(user)
    db.flush()
    db.add(Profile(user_id=user.id))
    db.commit()
    return user

def test_login_success(client, db):
    create_test_user(db)
    r = client.post("/auth/login", data={"email": "test@test.com", "password": "test123"}, follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/"

def test_login_wrong_password(client, db):
    create_test_user(db)
    r = client.post("/auth/login", data={"email": "test@test.com", "password": "errado"})
    assert r.status_code == 400

def test_dashboard_requires_auth(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 302

def test_logout(client, db):
    create_test_user(db)
    client.post("/auth/login", data={"email": "test@test.com", "password": "test123"})
    r = client.get("/auth/logout", follow_redirects=False)
    assert r.status_code == 302
```

- [ ] Rodar: `pytest tests/ -v`
- [ ] Commit: `git commit -m "test: setup de testes e auth tests"`
