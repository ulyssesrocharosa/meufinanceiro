from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.models import (
    Account, AccountType, Notification, Transaction,
    TransactionStatus, TransactionType, User,
)

router = APIRouter(prefix="/accounts", tags=["accounts"])
templates = Jinja2Templates(directory="app/templates")


def _ctx(request: Request, user: User, db: Session) -> dict:
    unread = db.query(Notification).filter_by(user_id=user.id, is_read=False).count()
    return {"request": request, "user": user, "unread_count": unread}


@router.get("", response_class=HTMLResponse)
def list_accounts(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    accounts = (
        db.query(Account)
        .filter_by(user_id=user.id)
        .order_by(Account.is_active.desc(), Account.name)
        .all()
    )
    total_balance = sum(a.balance for a in accounts if a.is_active)
    return templates.TemplateResponse(
        "accounts/list.html",
        {**_ctx(request, user, db), "accounts": accounts, "total_balance": total_balance,
         "account_types": [t.value for t in AccountType]},
    )


@router.get("/new", response_class=HTMLResponse)
def new_account_form(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        "accounts/form.html",
        {**_ctx(request, user, db), "account": None,
         "account_types": [t.value for t in AccountType]},
    )


@router.post("")
def create_account(
    request: Request,
    name: str = Form(...),
    type: str = Form(...),
    balance: float = Form(0.0),
    institution: Optional[str] = Form(None),
    account_number: Optional[str] = Form(None),
    color: str = Form("#3B82F6"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = Account(
        user_id=user.id,
        name=name.strip(),
        type=AccountType(type),
        balance=balance,
        institution=institution or None,
        account_number=account_number or None,
        color=color,
    )
    db.add(account)
    db.commit()
    return RedirectResponse("/accounts?success=Conta criada com sucesso", status_code=302)


@router.get("/{account_id}/edit", response_class=HTMLResponse)
def edit_account_form(
    account_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = db.query(Account).filter_by(id=account_id, user_id=user.id).first()
    if not account:
        return RedirectResponse("/accounts?error=Conta não encontrada", status_code=302)
    return templates.TemplateResponse(
        "accounts/form.html",
        {**_ctx(request, user, db), "account": account,
         "account_types": [t.value for t in AccountType]},
    )


@router.post("/{account_id}/edit")
def update_account(
    account_id: int,
    name: str = Form(...),
    type: str = Form(...),
    institution: Optional[str] = Form(None),
    account_number: Optional[str] = Form(None),
    color: str = Form("#3B82F6"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = db.query(Account).filter_by(id=account_id, user_id=user.id).first()
    if not account:
        return RedirectResponse("/accounts?error=Conta não encontrada", status_code=302)
    account.name = name.strip()
    account.type = AccountType(type)
    account.institution = institution or None
    account.account_number = account_number or None
    account.color = color
    db.commit()
    return RedirectResponse("/accounts?success=Conta atualizada", status_code=302)


@router.post("/{account_id}/toggle")
def toggle_account(
    account_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = db.query(Account).filter_by(id=account_id, user_id=user.id).first()
    if account:
        account.is_active = not account.is_active
        db.commit()
        msg = "Conta ativada" if account.is_active else "Conta desativada"
        return RedirectResponse(f"/accounts?success={msg}", status_code=302)
    return RedirectResponse("/accounts?error=Conta não encontrada", status_code=302)


@router.get("/{account_id}/transfer", response_class=HTMLResponse)
def transfer_form(
    account_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = db.query(Account).filter_by(id=account_id, user_id=user.id, is_active=True).first()
    if not account:
        return RedirectResponse("/accounts?error=Conta não encontrada", status_code=302)
    other_accounts = (
        db.query(Account)
        .filter(Account.user_id == user.id, Account.is_active == True, Account.id != account_id)
        .all()
    )
    return templates.TemplateResponse(
        "accounts/transfer.html",
        {**_ctx(request, user, db), "account": account, "other_accounts": other_accounts,
         "today": date.today().isoformat()},
    )


@router.post("/{account_id}/transfer")
def do_transfer(
    account_id: int,
    to_account_id: int = Form(...),
    amount: float = Form(...),
    description: Optional[str] = Form(None),
    transfer_date: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from_acc = db.query(Account).filter_by(id=account_id, user_id=user.id, is_active=True).first()
    to_acc = db.query(Account).filter_by(id=to_account_id, user_id=user.id, is_active=True).first()
    if not from_acc or not to_acc:
        return RedirectResponse("/accounts?error=Conta inválida", status_code=302)
    if amount <= 0:
        return RedirectResponse(f"/accounts/{account_id}/transfer?error=Valor inválido", status_code=302)

    d = date.fromisoformat(transfer_date)
    desc_out = description or f"Transferência para {to_acc.name}"
    desc_in = description or f"Transferência de {from_acc.name}"

    db.add(Transaction(
        user_id=user.id, account_id=from_acc.id, amount=amount,
        type=TransactionType.transfer, description=desc_out,
        date=d, status=TransactionStatus.completed,
    ))
    db.add(Transaction(
        user_id=user.id, account_id=to_acc.id, amount=amount,
        type=TransactionType.transfer, description=desc_in,
        date=d, status=TransactionStatus.completed,
    ))
    from_acc.balance -= amount
    to_acc.balance += amount
    db.commit()
    return RedirectResponse("/accounts?success=Transferência realizada com sucesso", status_code=302)
