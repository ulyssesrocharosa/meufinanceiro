import calendar
from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import Account, Category, Debt, Investment, Transaction, TransactionType


def monthly_summary(user_id: int, year: int, month: int, db: Session) -> dict:
    """Income, expense, net for a given year/month. Returns: {income, expense, net, transactions}"""
    start = date(year, month, 1)
    end = date(year, month, calendar.monthrange(year, month)[1])

    income = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.income,
            Transaction.date >= start,
            Transaction.date <= end,
        )
        .scalar()
        or 0.0
    )

    expense = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.expense,
            Transaction.date >= start,
            Transaction.date <= end,
        )
        .scalar()
        or 0.0
    )

    transactions = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.date >= start,
            Transaction.date <= end,
        )
        .order_by(Transaction.date.desc())
        .limit(50)
        .all()
    )

    return {
        "income": income,
        "expense": expense,
        "net": income - expense,
        "transactions": transactions,
    }


def spending_by_category(user_id: int, start: date, end: date, db: Session) -> list:
    """Returns list of {category_name, color, total} sorted desc by total, for expense transactions in period"""
    rows = (
        db.query(
            Category.name,
            Category.color,
            func.sum(Transaction.amount).label("total"),
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.expense,
            Transaction.date >= start,
            Transaction.date <= end,
        )
        .group_by(Category.id)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )
    return [{"name": r.name, "color": r.color, "total": r.total} for r in rows]


def income_vs_expense(user_id: int, months: int, db: Session) -> list:
    """Returns list of {month: 'Jan/25', income: float, expense: float} for the last N months"""
    today = date.today()
    result = []

    for i in range(months - 1, -1, -1):
        ref = today.replace(day=1)
        m = ref.month - i
        y = ref.year
        while m <= 0:
            m += 12
            y -= 1

        start = date(y, m, 1)
        end = date(y, m, calendar.monthrange(y, m)[1])

        inc = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == TransactionType.income,
                Transaction.date >= start,
                Transaction.date <= end,
            )
            .scalar()
            or 0.0
        )

        exp = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == TransactionType.expense,
                Transaction.date >= start,
                Transaction.date <= end,
            )
            .scalar()
            or 0.0
        )

        result.append({"month": start.strftime("%b/%y"), "income": inc, "expense": exp})

    return result


def net_worth(user_id: int, db: Session) -> dict:
    """Total assets (accounts balance + investments current_value) minus active debts"""
    accounts = db.query(Account).filter_by(user_id=user_id, is_active=True).all()
    total_accounts = sum(a.balance for a in accounts)

    investments = db.query(Investment).filter_by(user_id=user_id).all()
    total_investments = sum(i.current_value or i.amount for i in investments)

    debts = db.query(Debt).filter_by(user_id=user_id, status="active").all()
    total_debts = sum(d.current_amount for d in debts)

    return {
        "total_accounts": total_accounts,
        "total_investments": total_investments,
        "total_debts": total_debts,
        "net_worth": total_accounts + total_investments - total_debts,
        "accounts": accounts,
        "investments": investments,
        "debts": debts,
    }
