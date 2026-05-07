from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.models import (
    Account, Category, CategoryType, Notification, Transaction,
    TransactionStatus, TransactionType, User,
)
from .service import apply_to_balance

router = APIRouter(prefix="/transactions", tags=["transactions"])
templates = Jinja2Templates(directory="app/templates")


def _ctx(request: Request, user: User, db: Session) -> dict:
    unread = db.query(Notification).filter_by(user_id=user.id, is_read=False).count()
    return {"request": request, "user": user, "unread_count": unread}


@router.get("", response_class=HTMLResponse)
def list_transactions(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    tipo: Optional[str] = Query(None),
    account_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    mes: Optional[str] = Query(None),   # formato YYYY-MM
    busca: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
):
    q = db.query(Transaction).filter_by(user_id=user.id)

    if tipo:
        q = q.filter(Transaction.type == TransactionType(tipo))
    if account_id:
        q = q.filter(Transaction.account_id == account_id)
    if category_id:
        q = q.filter(Transaction.category_id == category_id)
    if mes:
        try:
            year, month = map(int, mes.split("-"))
            from calendar import monthrange
            last = monthrange(year, month)[1]
            q = q.filter(
                Transaction.date >= date(year, month, 1),
                Transaction.date <= date(year, month, last),
            )
        except ValueError:
            pass
    if busca:
        q = q.filter(Transaction.description.ilike(f"%{busca}%"))

    total = q.count()
    per_page = 25
    transactions = (
        q.order_by(Transaction.date.desc(), Transaction.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    accounts = db.query(Account).filter_by(user_id=user.id, is_active=True).order_by(Account.name).all()
    categories = db.query(Category).filter(
        (Category.user_id == user.id) | (Category.is_system == True)
    ).order_by(Category.name).all()

    return templates.TemplateResponse("transactions/list.html", {
        **_ctx(request, user, db),
        "transactions": transactions,
        "accounts": accounts,
        "categories": categories,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total + per_page - 1) // per_page),
        "filters": {"tipo": tipo, "account_id": account_id, "category_id": category_id,
                    "mes": mes, "busca": busca},
    })


@router.get("/new", response_class=HTMLResponse)
def new_transaction_form(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    accounts = db.query(Account).filter_by(user_id=user.id, is_active=True).order_by(Account.name).all()
    categories = db.query(Category).filter(
        (Category.user_id == user.id) | (Category.is_system == True)
    ).order_by(Category.type, Category.name).all()
    return templates.TemplateResponse("transactions/form.html", {
        **_ctx(request, user, db),
        "transaction": None,
        "accounts": accounts,
        "categories": categories,
        "transaction_types": [t.value for t in TransactionType],
        "transaction_statuses": [s.value for s in TransactionStatus],
        "today": date.today().isoformat(),
    })


@router.post("")
def create_transaction(
    request: Request,
    account_id: int = Form(...),
    amount: float = Form(...),
    type: str = Form(...),
    description: Optional[str] = Form(None),
    transaction_date: str = Form(...),
    status: str = Form("completed"),
    category_id: Optional[int] = Form(None),
    payment_method: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = db.query(Account).filter_by(id=account_id, user_id=user.id).first()
    if not account:
        return RedirectResponse("/transactions?error=Conta inválida", status_code=302)

    t = Transaction(
        user_id=user.id,
        account_id=account_id,
        amount=abs(amount),
        type=TransactionType(type),
        description=description or None,
        date=date.fromisoformat(transaction_date),
        status=TransactionStatus(status),
        category_id=category_id or None,
        payment_method=payment_method or None,
    )
    db.add(t)

    if TransactionStatus(status) == TransactionStatus.completed:
        apply_to_balance(account, abs(amount), TransactionType(type))

    db.commit()
    return RedirectResponse("/transactions?success=Transação criada", status_code=302)


@router.get("/{tid}/edit", response_class=HTMLResponse)
def edit_transaction_form(
    tid: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    t = db.query(Transaction).filter_by(id=tid, user_id=user.id).first()
    if not t:
        return RedirectResponse("/transactions?error=Transação não encontrada", status_code=302)
    accounts = db.query(Account).filter_by(user_id=user.id, is_active=True).order_by(Account.name).all()
    categories = db.query(Category).filter(
        (Category.user_id == user.id) | (Category.is_system == True)
    ).order_by(Category.type, Category.name).all()
    return templates.TemplateResponse("transactions/form.html", {
        **_ctx(request, user, db),
        "transaction": t,
        "accounts": accounts,
        "categories": categories,
        "transaction_types": [t2.value for t2 in TransactionType],
        "transaction_statuses": [s.value for s in TransactionStatus],
        "today": date.today().isoformat(),
    })


@router.post("/{tid}/edit")
def update_transaction(
    tid: int,
    account_id: int = Form(...),
    amount: float = Form(...),
    type: str = Form(...),
    description: Optional[str] = Form(None),
    transaction_date: str = Form(...),
    status: str = Form("completed"),
    category_id: Optional[int] = Form(None),
    payment_method: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    t = db.query(Transaction).filter_by(id=tid, user_id=user.id).first()
    if not t:
        return RedirectResponse("/transactions?error=Transação não encontrada", status_code=302)

    old_account = db.query(Account).filter_by(id=t.account_id, user_id=user.id).first()
    new_account = db.query(Account).filter_by(id=account_id, user_id=user.id).first()
    if not new_account:
        return RedirectResponse("/transactions?error=Conta inválida", status_code=302)

    # Reverter efeito antigo
    if t.status == TransactionStatus.completed and old_account:
        apply_to_balance(old_account, t.amount, t.type, reverse=True)

    # Aplicar novo efeito
    new_status = TransactionStatus(status)
    if new_status == TransactionStatus.completed:
        apply_to_balance(new_account, abs(amount), TransactionType(type))

    t.account_id = account_id
    t.amount = abs(amount)
    t.type = TransactionType(type)
    t.description = description or None
    t.date = date.fromisoformat(transaction_date)
    t.status = new_status
    t.category_id = category_id or None
    t.payment_method = payment_method or None

    db.commit()
    return RedirectResponse("/transactions?success=Transação atualizada", status_code=302)


@router.post("/{tid}/delete")
def delete_transaction(
    tid: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    t = db.query(Transaction).filter_by(id=tid, user_id=user.id).first()
    if not t:
        return RedirectResponse("/transactions?error=Transação não encontrada", status_code=302)

    account = db.query(Account).filter_by(id=t.account_id, user_id=user.id).first()
    if t.status == TransactionStatus.completed and account:
        apply_to_balance(account, t.amount, t.type, reverse=True)

    db.delete(t)
    db.commit()
    return RedirectResponse("/transactions?success=Transação excluída", status_code=302)
