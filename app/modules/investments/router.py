from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.models import Account, Investment, InvestmentType, Notification, RiskLevel, User

router = APIRouter(prefix="/investments", tags=["investments"])
templates = Jinja2Templates(directory="app/templates")


def _ctx(request: Request, user: User, db: Session) -> dict:
    unread = db.query(Notification).filter_by(user_id=user.id, is_read=False).count()
    return {"request": request, "user": user, "unread_count": unread}


def _inv_data(inv: Investment) -> dict:
    if inv.current_value is not None and inv.amount > 0:
        rentability = round((inv.current_value - inv.amount) / inv.amount * 100, 2)
        gain = inv.current_value - inv.amount
    else:
        rentability = None
        gain = None
    return {"inv": inv, "rentability": rentability, "gain": gain}


@router.get("", response_class=HTMLResponse)
def list_investments(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    investments = (
        db.query(Investment)
        .filter_by(user_id=user.id)
        .order_by(Investment.purchase_date.desc())
        .all()
    )
    inv_data = [_inv_data(i) for i in investments]
    total_invested = sum(i.amount for i in investments)
    total_current = sum(i.current_value for i in investments if i.current_value is not None)
    return templates.TemplateResponse("investments/list.html", {
        **_ctx(request, user, db),
        "inv_data": inv_data,
        "total_invested": total_invested,
        "total_current": total_current,
    })


@router.get("/new", response_class=HTMLResponse)
def new_investment_form(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    accounts = db.query(Account).filter_by(user_id=user.id, is_active=True).order_by(Account.name).all()
    return templates.TemplateResponse("investments/form.html", {
        **_ctx(request, user, db),
        "investment": None,
        "accounts": accounts,
        "inv_types": [t.value for t in InvestmentType],
        "risk_levels": [r.value for r in RiskLevel],
        "today": date.today().isoformat(),
    })


@router.post("")
def create_investment(
    name: str = Form(...),
    account_id: int = Form(...),
    type: Optional[str] = Form(None),
    amount: float = Form(...),
    current_value: Optional[float] = Form(None),
    purchase_date: str = Form(...),
    risk_level: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inv = Investment(
        user_id=user.id,
        account_id=account_id,
        name=name.strip(),
        type=InvestmentType(type) if type else None,
        amount=abs(amount),
        current_value=abs(current_value) if current_value is not None else None,
        purchase_date=date.fromisoformat(purchase_date),
        risk_level=RiskLevel(risk_level) if risk_level else None,
    )
    db.add(inv)
    db.commit()
    return RedirectResponse("/investments?success=Investimento criado", status_code=302)


@router.get("/{inv_id}/edit", response_class=HTMLResponse)
def edit_investment_form(
    inv_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inv = db.query(Investment).filter_by(id=inv_id, user_id=user.id).first()
    if not inv:
        return RedirectResponse("/investments?error=Não encontrado", status_code=302)
    accounts = db.query(Account).filter_by(user_id=user.id, is_active=True).order_by(Account.name).all()
    return templates.TemplateResponse("investments/form.html", {
        **_ctx(request, user, db),
        "investment": inv,
        "accounts": accounts,
        "inv_types": [t.value for t in InvestmentType],
        "risk_levels": [r.value for r in RiskLevel],
        "today": date.today().isoformat(),
    })


@router.post("/{inv_id}/edit")
def update_investment(
    inv_id: int,
    name: str = Form(...),
    account_id: int = Form(...),
    type: Optional[str] = Form(None),
    amount: float = Form(...),
    current_value: Optional[float] = Form(None),
    purchase_date: str = Form(...),
    risk_level: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inv = db.query(Investment).filter_by(id=inv_id, user_id=user.id).first()
    if not inv:
        return RedirectResponse("/investments?error=Não encontrado", status_code=302)
    inv.name = name.strip()
    inv.account_id = account_id
    inv.type = InvestmentType(type) if type else None
    inv.amount = abs(amount)
    inv.current_value = abs(current_value) if current_value is not None else None
    inv.purchase_date = date.fromisoformat(purchase_date)
    inv.risk_level = RiskLevel(risk_level) if risk_level else None
    db.commit()
    return RedirectResponse("/investments?success=Investimento atualizado", status_code=302)


@router.post("/{inv_id}/delete")
def delete_investment(
    inv_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inv = db.query(Investment).filter_by(id=inv_id, user_id=user.id).first()
    if inv:
        db.delete(inv)
        db.commit()
        return RedirectResponse("/investments?success=Excluído", status_code=302)
    return RedirectResponse("/investments?error=Não encontrado", status_code=302)
