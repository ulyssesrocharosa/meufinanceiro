from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.models import (
    Budget, BudgetPeriod, Category, Notification,
    Transaction, TransactionStatus, TransactionType, User,
)

router = APIRouter(prefix="/budgets", tags=["budgets"])
templates = Jinja2Templates(directory="app/templates")


def _ctx(request: Request, user: User, db: Session) -> dict:
    unread = db.query(Notification).filter_by(user_id=user.id, is_read=False).count()
    return {"request": request, "user": user, "unread_count": unread}


def _calc_spent(budget: Budget, db: Session) -> float:
    return db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == budget.user_id,
        Transaction.category_id == budget.category_id,
        Transaction.type == TransactionType.expense,
        Transaction.status == TransactionStatus.completed,
        Transaction.date >= budget.start_date,
        Transaction.date <= budget.end_date,
    ).scalar() or 0.0


@router.get("", response_class=HTMLResponse)
def list_budgets(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today()
    budgets = (
        db.query(Budget)
        .filter_by(user_id=user.id)
        .order_by(Budget.end_date.desc())
        .all()
    )
    budgets_data = []
    for b in budgets:
        spent = _calc_spent(b, db)
        pct = min(100.0, round(spent / b.amount * 100, 1)) if b.amount > 0 else 0.0
        is_active = b.start_date <= today <= b.end_date
        budgets_data.append({"budget": b, "spent": spent, "pct": pct, "is_active": is_active})

    return templates.TemplateResponse("budgets/list.html", {
        **_ctx(request, user, db),
        "budgets_data": budgets_data,
    })


@router.get("/new", response_class=HTMLResponse)
def new_budget_form(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    categories = db.query(Category).filter(
        (Category.user_id == user.id) | (Category.is_system == True)
    ).order_by(Category.name).all()
    today = date.today()
    return templates.TemplateResponse("budgets/form.html", {
        **_ctx(request, user, db),
        "budget": None,
        "categories": categories,
        "periods": [p.value for p in BudgetPeriod],
        "today": today.isoformat(),
        "first_day": today.replace(day=1).isoformat(),
    })


@router.post("")
def create_budget(
    category_id: int = Form(...),
    amount: float = Form(...),
    period: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sd = date.fromisoformat(start_date)
    ed = date.fromisoformat(end_date)
    if ed <= sd:
        return RedirectResponse("/budgets/new?error=Data fim deve ser após data início", status_code=302)
    budget = Budget(
        user_id=user.id,
        category_id=category_id,
        amount=abs(amount),
        period=BudgetPeriod(period),
        start_date=sd,
        end_date=ed,
    )
    db.add(budget)
    db.commit()
    return RedirectResponse("/budgets?success=Orçamento criado", status_code=302)


@router.get("/{budget_id}/edit", response_class=HTMLResponse)
def edit_budget_form(
    budget_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budget = db.query(Budget).filter_by(id=budget_id, user_id=user.id).first()
    if not budget:
        return RedirectResponse("/budgets?error=Orçamento não encontrado", status_code=302)
    categories = db.query(Category).filter(
        (Category.user_id == user.id) | (Category.is_system == True)
    ).order_by(Category.name).all()
    today = date.today()
    return templates.TemplateResponse("budgets/form.html", {
        **_ctx(request, user, db),
        "budget": budget,
        "categories": categories,
        "periods": [p.value for p in BudgetPeriod],
        "today": today.isoformat(),
        "first_day": today.replace(day=1).isoformat(),
    })


@router.post("/{budget_id}/edit")
def update_budget(
    budget_id: int,
    category_id: int = Form(...),
    amount: float = Form(...),
    period: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budget = db.query(Budget).filter_by(id=budget_id, user_id=user.id).first()
    if not budget:
        return RedirectResponse("/budgets?error=Não encontrado", status_code=302)
    budget.category_id = category_id
    budget.amount = abs(amount)
    budget.period = BudgetPeriod(period)
    budget.start_date = date.fromisoformat(start_date)
    budget.end_date = date.fromisoformat(end_date)
    db.commit()
    return RedirectResponse("/budgets?success=Orçamento atualizado", status_code=302)


@router.post("/{budget_id}/delete")
def delete_budget(
    budget_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budget = db.query(Budget).filter_by(id=budget_id, user_id=user.id).first()
    if budget:
        db.delete(budget)
        db.commit()
        return RedirectResponse("/budgets?success=Orçamento excluído", status_code=302)
    return RedirectResponse("/budgets?error=Não encontrado", status_code=302)
