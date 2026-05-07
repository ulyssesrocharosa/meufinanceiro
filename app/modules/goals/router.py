from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.models import Account, Goal, GoalPriority, Notification, User

router = APIRouter(prefix="/goals", tags=["goals"])
templates = Jinja2Templates(directory="app/templates")


def _ctx(request: Request, user: User, db: Session) -> dict:
    unread = db.query(Notification).filter_by(user_id=user.id, is_read=False).count()
    return {"request": request, "user": user, "unread_count": unread}


@router.get("", response_class=HTMLResponse)
def list_goals(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goals = (
        db.query(Goal)
        .filter_by(user_id=user.id)
        .order_by(Goal.target_date)
        .all()
    )
    today = date.today()
    goals_data = []
    for g in goals:
        pct = min(100.0, round(g.current_amount / g.target_amount * 100, 1)) if g.target_amount > 0 else 0.0
        days_left = (g.target_date - today).days
        goals_data.append({"goal": g, "pct": pct, "days_left": days_left})
    return templates.TemplateResponse("goals/list.html", {
        **_ctx(request, user, db),
        "goals_data": goals_data,
        "today": today,
    })


@router.get("/new", response_class=HTMLResponse)
def new_goal_form(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    accounts = db.query(Account).filter_by(user_id=user.id, is_active=True).order_by(Account.name).all()
    return templates.TemplateResponse("goals/form.html", {
        **_ctx(request, user, db),
        "goal": None,
        "accounts": accounts,
        "priorities": [p.value for p in GoalPriority],
        "today": date.today().isoformat(),
    })


@router.post("")
def create_goal(
    name: str = Form(...),
    target_amount: float = Form(...),
    current_amount: float = Form(0.0),
    target_date: str = Form(...),
    priority: str = Form("medium"),
    account_id: Optional[int] = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = Goal(
        user_id=user.id,
        name=name.strip(),
        target_amount=abs(target_amount),
        current_amount=max(0.0, current_amount),
        target_date=date.fromisoformat(target_date),
        priority=GoalPriority(priority),
        account_id=account_id or None,
    )
    db.add(goal)
    db.commit()
    return RedirectResponse("/goals?success=Meta criada com sucesso", status_code=302)


@router.get("/{goal_id}/edit", response_class=HTMLResponse)
def edit_goal_form(
    goal_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = db.query(Goal).filter_by(id=goal_id, user_id=user.id).first()
    if not goal:
        return RedirectResponse("/goals?error=Meta não encontrada", status_code=302)
    accounts = db.query(Account).filter_by(user_id=user.id, is_active=True).order_by(Account.name).all()
    return templates.TemplateResponse("goals/form.html", {
        **_ctx(request, user, db),
        "goal": goal,
        "accounts": accounts,
        "priorities": [p.value for p in GoalPriority],
        "today": date.today().isoformat(),
    })


@router.post("/{goal_id}/edit")
def update_goal(
    goal_id: int,
    name: str = Form(...),
    target_amount: float = Form(...),
    current_amount: float = Form(0.0),
    target_date: str = Form(...),
    priority: str = Form("medium"),
    account_id: Optional[int] = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = db.query(Goal).filter_by(id=goal_id, user_id=user.id).first()
    if not goal:
        return RedirectResponse("/goals?error=Meta não encontrada", status_code=302)
    goal.name = name.strip()
    goal.target_amount = abs(target_amount)
    goal.current_amount = max(0.0, current_amount)
    goal.target_date = date.fromisoformat(target_date)
    goal.priority = GoalPriority(priority)
    goal.account_id = account_id or None
    db.commit()
    return RedirectResponse("/goals?success=Meta atualizada", status_code=302)


@router.post("/{goal_id}/contribute")
def contribute_to_goal(
    goal_id: int,
    amount: float = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = db.query(Goal).filter_by(id=goal_id, user_id=user.id).first()
    if not goal:
        return RedirectResponse("/goals?error=Meta não encontrada", status_code=302)
    goal.current_amount = min(goal.target_amount, goal.current_amount + abs(amount))
    db.commit()
    return RedirectResponse("/goals?success=Contribuição adicionada", status_code=302)


@router.post("/{goal_id}/delete")
def delete_goal(
    goal_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = db.query(Goal).filter_by(id=goal_id, user_id=user.id).first()
    if goal:
        db.delete(goal)
        db.commit()
        return RedirectResponse("/goals?success=Meta excluída", status_code=302)
    return RedirectResponse("/goals?error=Meta não encontrada", status_code=302)
