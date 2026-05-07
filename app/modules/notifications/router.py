from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.models import User, Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])
templates = Jinja2Templates(directory="app/templates")


def _ctx(request, user, db):
    unread = db.query(Notification).filter_by(user_id=user.id, is_read=False).count()
    return {"request": request, "user": user, "unread_count": unread}


@router.get("", response_class=HTMLResponse)
def list_notifications(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    unread = (
        db.query(Notification)
        .filter_by(user_id=user.id, is_read=False)
        .order_by(Notification.created_at.desc())
        .all()
    )
    read = (
        db.query(Notification)
        .filter_by(user_id=user.id, is_read=True)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return templates.TemplateResponse(
        "notifications/index.html",
        {
            **_ctx(request, user, db),
            "unread_notifications": unread,
            "read_notifications": read,
        },
    )


@router.post("/{notif_id}/read")
def mark_read(
    notif_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notif = db.query(Notification).filter_by(id=notif_id, user_id=user.id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return RedirectResponse("/notifications", status_code=302)


@router.post("/read-all")
def mark_all_read(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(Notification).filter_by(user_id=user.id, is_read=False).update(
        {"is_read": True}
    )
    db.commit()
    return RedirectResponse(
        "/notifications?success=Todas marcadas como lidas", status_code=302
    )


@router.post("/{notif_id}/delete")
def delete_notification(
    notif_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notif = db.query(Notification).filter_by(id=notif_id, user_id=user.id).first()
    if notif:
        db.delete(notif)
        db.commit()
    return RedirectResponse("/notifications", status_code=302)
