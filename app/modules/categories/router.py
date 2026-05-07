from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.models import Category, CategoryType, Notification, User

router = APIRouter(prefix="/categories", tags=["categories"])
templates = Jinja2Templates(directory="app/templates")


def _ctx(request: Request, user: User, db: Session) -> dict:
    unread = db.query(Notification).filter_by(user_id=user.id, is_read=False).count()
    return {"request": request, "user": user, "unread_count": unread}


@router.get("", response_class=HTMLResponse)
def list_categories(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    system_cats = (
        db.query(Category)
        .filter_by(is_system=True)
        .order_by(Category.type, Category.name)
        .all()
    )
    user_cats = (
        db.query(Category)
        .filter_by(user_id=user.id, is_system=False)
        .order_by(Category.type, Category.name)
        .all()
    )
    return templates.TemplateResponse(
        "categories/list.html",
        {**_ctx(request, user, db), "system_cats": system_cats, "user_cats": user_cats,
         "category_types": [t.value for t in CategoryType]},
    )


@router.get("/new", response_class=HTMLResponse)
def new_category_form(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_cats = db.query(Category).filter(
        (Category.user_id == user.id) | (Category.is_system == True)
    ).order_by(Category.name).all()
    return templates.TemplateResponse(
        "categories/form.html",
        {**_ctx(request, user, db), "category": None,
         "category_types": [t.value for t in CategoryType],
         "parent_options": user_cats},
    )


@router.post("")
def create_category(
    request: Request,
    name: str = Form(...),
    type: str = Form(...),
    icon: str = Form("dollar-sign"),
    color: str = Form("#6B7280"),
    parent_id: Optional[int] = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cat = Category(
        user_id=user.id,
        name=name.strip(),
        type=CategoryType(type),
        icon=icon.strip() or "dollar-sign",
        color=color,
        parent_id=parent_id or None,
        is_system=False,
    )
    db.add(cat)
    db.commit()
    return RedirectResponse("/categories?success=Categoria criada com sucesso", status_code=302)


@router.get("/{cat_id}/edit", response_class=HTMLResponse)
def edit_category_form(
    cat_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cat = db.query(Category).filter_by(id=cat_id, user_id=user.id, is_system=False).first()
    if not cat:
        return RedirectResponse("/categories?error=Categoria não encontrada ou não editável", status_code=302)
    parent_options = db.query(Category).filter(
        (Category.user_id == user.id) | (Category.is_system == True),
        Category.id != cat_id,
    ).order_by(Category.name).all()
    return templates.TemplateResponse(
        "categories/form.html",
        {**_ctx(request, user, db), "category": cat,
         "category_types": [t.value for t in CategoryType],
         "parent_options": parent_options},
    )


@router.post("/{cat_id}/edit")
def update_category(
    cat_id: int,
    name: str = Form(...),
    type: str = Form(...),
    icon: str = Form("dollar-sign"),
    color: str = Form("#6B7280"),
    parent_id: Optional[int] = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cat = db.query(Category).filter_by(id=cat_id, user_id=user.id, is_system=False).first()
    if not cat:
        return RedirectResponse("/categories?error=Categoria não encontrada", status_code=302)
    cat.name = name.strip()
    cat.type = CategoryType(type)
    cat.icon = icon.strip() or "dollar-sign"
    cat.color = color
    cat.parent_id = parent_id or None
    db.commit()
    return RedirectResponse("/categories?success=Categoria atualizada", status_code=302)


@router.post("/{cat_id}/delete")
def delete_category(
    cat_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cat = db.query(Category).filter_by(id=cat_id, user_id=user.id, is_system=False).first()
    if not cat:
        return RedirectResponse("/categories?error=Categoria não encontrada ou não deletável", status_code=302)
    db.delete(cat)
    db.commit()
    return RedirectResponse("/categories?success=Categoria excluída", status_code=302)
