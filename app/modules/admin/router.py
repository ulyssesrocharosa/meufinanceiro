from typing import Optional
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.auth import require_admin
from app.core.security import hash_password
from app.core.database import get_db
from app.models.models import User, Profile, UserRole, Notification

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")


def _ctx(request, user, db):
    unread = db.query(Notification).filter_by(user_id=user.id, is_read=False).count()
    return {"request": request, "user": user, "unread_count": unread}


@router.get("", response_class=HTMLResponse)
def admin_index(
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return templates.TemplateResponse(
        "admin/index.html",
        {**_ctx(request, user, db), "users": users},
    )


@router.get("/users/new", response_class=HTMLResponse)
def new_user_form(
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        "admin/user_form.html",
        {**_ctx(request, user, db), "edit_user": None},
    )


@router.post("/users")
def create_user(
    email: str = Form(...),
    name: str = Form(...),
    password: str = Form(...),
    role: str = Form("user"),
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if db.query(User).filter_by(email=email.strip().lower()).first():
        return RedirectResponse("/admin?error=Email já cadastrado", status_code=302)
    new_user = User(
        email=email.strip().lower(),
        name=name.strip(),
        password_hash=hash_password(password),
        role=UserRole(role),
        is_active=True,
    )
    db.add(new_user)
    db.flush()
    db.add(Profile(user_id=new_user.id))
    db.commit()
    return RedirectResponse("/admin?success=Usuário criado", status_code=302)


@router.post("/users/{user_id}/toggle")
def toggle_user(
    user_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target = db.query(User).filter_by(id=user_id).first()
    if not target:
        return RedirectResponse("/admin?error=Usuário não encontrado", status_code=302)
    if target.id == user.id:
        return RedirectResponse(
            "/admin?error=Não pode desativar a si mesmo", status_code=302
        )
    target.is_active = not target.is_active
    db.commit()
    status = "ativado" if target.is_active else "desativado"
    return RedirectResponse(f"/admin?success=Usuário {status}", status_code=302)


@router.post("/users/{user_id}/reset-password")
def reset_password(
    user_id: int,
    new_password: str = Form(...),
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target = db.query(User).filter_by(id=user_id).first()
    if not target:
        return RedirectResponse("/admin?error=Usuário não encontrado", status_code=302)
    if len(new_password) < 6:
        return RedirectResponse(
            "/admin?error=Senha deve ter ao menos 6 caracteres", status_code=302
        )
    target.password_hash = hash_password(new_password)
    db.commit()
    return RedirectResponse("/admin?success=Senha redefinida", status_code=302)
