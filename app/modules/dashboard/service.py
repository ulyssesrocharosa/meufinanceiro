from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import (
    Account, Budget, RecurringBill, Transaction,
    TransactionType, TransactionStatus,
)


def get_dashboard_data(user_id: int, db: Session) -> dict:
    today = date.today()
    first_day = today.replace(day=1)

    # KPIs do mês atual
    def _sum(ttype: TransactionType, start: date, end: date) -> float:
        return db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == ttype,
            Transaction.status == TransactionStatus.completed,
            Transaction.date >= start,
            Transaction.date <= end,
        ).scalar() or 0.0

    month_income = _sum(TransactionType.income, first_day, today)
    month_expense = _sum(TransactionType.expense, first_day, today)

    total_balance = db.query(func.sum(Account.balance)).filter(
        Account.user_id == user_id,
        Account.is_active == True,
    ).scalar() or 0.0

    # Últimas 10 transações
    recent = (
        db.query(Transaction)
        .filter_by(user_id=user_id)
        .order_by(Transaction.date.desc(), Transaction.id.desc())
        .limit(10)
        .all()
    )

    # Contas vencendo nos próximos 7 dias
    upcoming = (
        db.query(RecurringBill)
        .filter(
            RecurringBill.user_id == user_id,
            RecurringBill.is_active == True,
            RecurringBill.next_occurrence <= today + timedelta(days=7),
            RecurringBill.next_occurrence >= today,
        )
        .order_by(RecurringBill.next_occurrence)
        .all()
    )

    # Dados dos últimos 6 meses para gráfico
    months_labels = []
    months_income = []
    months_expense = []

    for i in range(5, -1, -1):
        ref_month = today.month - i
        ref_year = today.year
        while ref_month <= 0:
            ref_month += 12
            ref_year -= 1

        from calendar import monthrange
        last_day = monthrange(ref_year, ref_month)[1]
        m_start = date(ref_year, ref_month, 1)
        m_end = date(ref_year, ref_month, last_day)

        months_labels.append(m_start.strftime("%b/%y"))
        months_income.append(_sum(TransactionType.income, m_start, m_end))
        months_expense.append(_sum(TransactionType.expense, m_start, m_end))

    # Gastos por categoria (mês atual) para pizza
    from app.models.models import Category
    from sqlalchemy import and_
    cat_data = (
        db.query(Category.name, Category.color, func.sum(Transaction.amount).label("total"))
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.expense,
            Transaction.status == TransactionStatus.completed,
            Transaction.date >= first_day,
            Transaction.date <= today,
        )
        .group_by(Category.id)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(8)
        .all()
    )

    # Orçamentos ativos com % gasta
    active_budgets = (
        db.query(Budget)
        .filter(
            Budget.user_id == user_id,
            Budget.start_date <= today,
            Budget.end_date >= today,
        )
        .all()
    )
    budgets_with_spent = []
    for b in active_budgets:
        spent = _sum(TransactionType.expense, b.start_date, b.end_date)
        pct = min(100, round(spent / b.amount * 100, 1)) if b.amount > 0 else 0
        budgets_with_spent.append({"budget": b, "spent": spent, "pct": pct})

    return {
        "total_balance": total_balance,
        "month_income": month_income,
        "month_expense": month_expense,
        "net": month_income - month_expense,
        "recent_transactions": recent,
        "upcoming_bills": upcoming,
        "months_labels": months_labels,
        "months_income": months_income,
        "months_expense": months_expense,
        "cat_names": [c.name for c in cat_data],
        "cat_colors": [c.color for c in cat_data],
        "cat_totals": [float(c.total) for c in cat_data],
        "budgets_with_spent": budgets_with_spent,
    }
