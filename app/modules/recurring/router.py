from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.models import (
    Account, Category, Notification, RecurringBill, RecurringFrequency,
    Transaction, TransactionStatus, TransactionType, User,
)
from .service import calc_next_occurrence

router = APIRouter(prefix="/recurring", tags=["recurring"])
templates = Jinja2Templates(directory="app/templates")


def _ctx(request: Request, user: User, db: Session) -> dict:
    unread = db.query(Notification).filter_by(user_id=user.id, is_read=False).count()
    return {"request": request, "user": user, "unread_count": unread}


@router.get("", response_class=HTMLResponse)
def list_recurring(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bills = (
        db.query(RecurringBill)
        .filter_by(user_id=user.id)
        .order_by(RecurringBill.is_active.desc(), RecurringBill.next_occurrence)
        .all()
    )
    today = date.today()
    return templates.TemplateResponse("recurring/list.html", {
        **_ctx(request, user, db),
        "bills": bills,
        "today": today,
    })


@router.get("/new", response_class=HTMLResponse)
def new_recurring_form(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    categories = db.query(Category).filter(
        (Category.user_id == user.id) | (Category.is_system == True)
    ).order_by(Category.name).all()
    accounts = db.query(Account).filter_by(user_id=user.id, is_active=True).order_by(Account.name).all()
    return templates.TemplateResponse("recurring/form.html", {
        **_ctx(request, user, db),
        "bill": None,
        "categories": categories,
        "accounts": accounts,
        "frequencies": [f.value for f in RecurringFrequency],
        "today": date.today().isoformat(),
    })


@router.post("")
def create_recurring(
    name: str = Form(...),
    amount: float = Form(...),
    frequency: str = Form(...),
    start_date: str = Form(...),
    end_date: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    days_before_reminder: int = Form(3),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sd = date.fromisoformat(start_date)
    bill = RecurringBill(
        user_id=user.id,
        name=name.strip(),
        amount=abs(amount),
        frequency=RecurringFrequency(frequency),
        start_date=sd,
        end_date=date.fromisoformat(end_date) if end_date else None,
        next_occurrence=sd,
        category_id=category_id or None,
        days_before_reminder=max(0, days_before_reminder),
        is_active=True,
    )
    db.add(bill)
    db.commit()
    return RedirectResponse("/recurring?success=Recorrente criado com sucesso", status_code=302)


@router.get("/{bill_id}/edit", response_class=HTMLResponse)
def edit_recurring_form(
    bill_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bill = db.query(RecurringBill).filter_by(id=bill_id, user_id=user.id).first()
    if not bill:
        return RedirectResponse("/recurring?error=Não encontrado", status_code=302)
    categories = db.query(Category).filter(
        (Category.user_id == user.id) | (Category.is_system == True)
    ).order_by(Category.name).all()
    accounts = db.query(Account).filter_by(user_id=user.id, is_active=True).order_by(Account.name).all()
    return templates.TemplateResponse("recurring/form.html", {
        **_ctx(request, user, db),
        "bill": bill,
        "categories": categories,
        "accounts": accounts,
        "frequencies": [f.value for f in RecurringFrequency],
        "today": date.today().isoformat(),
    })


@router.post("/{bill_id}/edit")
def update_recurring(
    bill_id: int,
    name: str = Form(...),
    amount: float = Form(...),
    frequency: str = Form(...),
    start_date: str = Form(...),
    end_date: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    days_before_reminder: int = Form(3),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bill = db.query(RecurringBill).filter_by(id=bill_id, user_id=user.id).first()
    if not bill:
        return RedirectResponse("/recurring?error=Não encontrado", status_code=302)
    bill.name = name.strip()
    bill.amount = abs(amount)
    bill.frequency = RecurringFrequency(frequency)
    bill.start_date = date.fromisoformat(start_date)
    bill.end_date = date.fromisoformat(end_date) if end_date else None
    bill.category_id = category_id or None
    bill.days_before_reminder = max(0, days_before_reminder)
    db.commit()
    return RedirectResponse("/recurring?success=Recorrente atualizado", status_code=302)


@router.post("/{bill_id}/toggle")
def toggle_recurring(
    bill_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bill = db.query(RecurringBill).filter_by(id=bill_id, user_id=user.id).first()
    if bill:
        bill.is_active = not bill.is_active
        db.commit()
        msg = "Ativado" if bill.is_active else "Desativado"
        return RedirectResponse(f"/recurring?success={msg}", status_code=302)
    return RedirectResponse("/recurring?error=Não encontrado", status_code=302)


@router.post("/{bill_id}/pay")
def pay_recurring(
    bill_id: int,
    account_id: int = Form(...),
    pay_date: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bill = db.query(RecurringBill).filter_by(id=bill_id, user_id=user.id, is_active=True).first()
    account = db.query(Account).filter_by(id=account_id, user_id=user.id, is_active=True).first()
    if not bill or not account:
        return RedirectResponse("/recurring?error=Dados inválidos", status_code=302)

    d = date.fromisoformat(pay_date)
    db.add(Transaction(
        user_id=user.id,
        account_id=account.id,
        amount=bill.amount,
        type=TransactionType.expense,
        description=f"Pagamento: {bill.name}",
        date=d,
        status=TransactionStatus.completed,
        category_id=bill.category_id,
        recurring_bill_id=bill.id,
    ))
    account.balance -= bill.amount
    bill.next_occurrence = calc_next_occurrence(bill.next_occurrence, bill.frequency)
    db.commit()
    return RedirectResponse("/recurring?success=Pagamento registrado", status_code=302)


@router.post("/{bill_id}/delete")
def delete_recurring(
    bill_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bill = db.query(RecurringBill).filter_by(id=bill_id, user_id=user.id).first()
    if bill:
        db.delete(bill)
        db.commit()
        return RedirectResponse("/recurring?success=Excluído", status_code=302)
    return RedirectResponse("/recurring?error=Não encontrado", status_code=302)
