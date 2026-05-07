from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.models import Notification, User
from .service import get_dashboard_data

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


def _ctx(request: Request, user: User, db: Session) -> dict:
    unread = db.query(Notification).filter_by(user_id=user.id, is_read=False).count()
    return {"request": request, "user": user, "unread_count": unread}


@router.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = get_dashboard_data(user.id, db)
    return templates.TemplateResponse(
        "dashboard/dashboard.html",
        {**_ctx(request, user, db), **data},
    )
