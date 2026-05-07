from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.models import Debt, DebtStatus, DebtType, Notification, User

router = APIRouter(prefix="/debts", tags=["debts"])
templates = Jinja2Templates(directory="app/templates")


def _ctx(request: Request, user: User, db: Session) -> dict:
    unread = db.query(Notification).filter_by(user_id=user.id, is_read=False).count()
    return {"request": request, "user": user, "unread_count": unread}


def _debt_data(debt: Debt) -> dict:
    paid = debt.original_amount - debt.current_amount
    pct = min(100.0, round(paid / debt.original_amount * 100, 1)) if debt.original_amount > 0 else 0.0
    return {"debt": debt, "paid": paid, "pct": pct}


@router.get("", response_class=HTMLResponse)
def list_debts(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    debts = (
        db.query(Debt)
        .filter_by(user_id=user.id)
        .order_by(Debt.status, Debt.due_date)
        .all()
    )
    debts_data = [_debt_data(d) for d in debts]
    total_debt = sum(d.current_amount for d in debts if d.status == DebtStatus.active)
    return templates.TemplateResponse("debts/list.html", {
        **_ctx(request, user, db),
        "debts_data": debts_data,
        "total_debt": total_debt,
        "today": date.today(),
    })


@router.get("/new", response_class=HTMLResponse)
def new_debt_form(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse("debts/form.html", {
        **_ctx(request, user, db),
        "debt": None,
        "debt_types": [t.value for t in DebtType],
        "debt_statuses": [s.value for s in DebtStatus],
        "today": date.today().isoformat(),
    })


@router.post("")
def create_debt(
    name: str = Form(...),
    original_amount: float = Form(...),
    current_amount: Optional[float] = Form(None),
    interest_rate: float = Form(0.0),
    type: Optional[str] = Form(None),
    due_date: Optional[str] = Form(None),
    status: str = Form("active"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    orig = abs(original_amount)
    curr = abs(current_amount) if current_amount is not None else orig
    debt = Debt(
        user_id=user.id,
        name=name.strip(),
        original_amount=orig,
        current_amount=min(curr, orig),
        interest_rate=max(0.0, interest_rate),
        type=DebtType(type) if type else None,
        due_date=date.fromisoformat(due_date) if due_date else None,
        status=DebtStatus(status),
    )
    db.add(debt)
    db.commit()
    return RedirectResponse("/debts?success=Dívida criada", status_code=302)


@router.get("/{debt_id}/edit", response_class=HTMLResponse)
def edit_debt_form(
    debt_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    debt = db.query(Debt).filter_by(id=debt_id, user_id=user.id).first()
    if not debt:
        return RedirectResponse("/debts?error=Dívida não encontrada", status_code=302)
    return templates.TemplateResponse("debts/form.html", {
        **_ctx(request, user, db),
        "debt": debt,
        "debt_types": [t.value for t in DebtType],
        "debt_statuses": [s.value for s in DebtStatus],
        "today": date.today().isoformat(),
    })


@router.post("/{debt_id}/edit")
def update_debt(
    debt_id: int,
    name: str = Form(...),
    original_amount: float = Form(...),
    current_amount: float = Form(...),
    interest_rate: float = Form(0.0),
    type: Optional[str] = Form(None),
    due_date: Optional[str] = Form(None),
    status: str = Form("active"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    debt = db.query(Debt).filter_by(id=debt_id, user_id=user.id).first()
    if not debt:
        return RedirectResponse("/debts?error=Dívida não encontrada", status_code=302)
    orig = abs(original_amount)
    debt.name = name.strip()
    debt.original_amount = orig
    debt.current_amount = min(abs(current_amount), orig)
    debt.interest_rate = max(0.0, interest_rate)
    debt.type = DebtType(type) if type else None
    debt.due_date = date.fromisoformat(due_date) if due_date else None
    debt.status = DebtStatus(status)
    db.commit()
    return RedirectResponse("/debts?success=Dívida atualizada", status_code=302)


@router.post("/{debt_id}/delete")
def delete_debt(
    debt_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    debt = db.query(Debt).filter_by(id=debt_id, user_id=user.id).first()
    if debt:
        db.delete(debt)
        db.commit()
        return RedirectResponse("/debts?success=Dívida excluída", status_code=302)
    return RedirectResponse("/debts?error=Dívida não encontrada", status_code=302)
