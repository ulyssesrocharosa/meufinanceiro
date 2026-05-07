from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.models import Notification, User

from .service import income_vs_expense, monthly_summary, net_worth, spending_by_category

router = APIRouter(prefix="/reports", tags=["reports"])
templates = Jinja2Templates(directory="app/templates")


def _ctx(request: Request, user: User, db: Session) -> dict:
    unread = db.query(Notification).filter_by(user_id=user.id, is_read=False).count()
    return {"request": request, "user": user, "unread_count": unread}


@router.get("", response_class=HTMLResponse)
def reports_index(
    request: Request,
    report_type: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    months: int = 6,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today()
    data: dict = {}
    error: Optional[str] = None

    if report_type == "monthly_summary":
        y = year or today.year
        m = month or today.month
        data = monthly_summary(user.id, y, m, db)
        data["year"] = y
        data["month"] = m

    elif report_type == "spending_by_category":
        try:
            s = date.fromisoformat(start) if start else date(today.year, today.month, 1)
            e = date.fromisoformat(end) if end else today
            data["categories"] = spending_by_category(user.id, s, e, db)
            data["start"] = s.isoformat()
            data["end"] = e.isoformat()
        except ValueError:
            error = "Datas inválidas"

    elif report_type == "income_vs_expense":
        data["chart"] = income_vs_expense(user.id, months, db)
        data["months"] = months

    elif report_type == "net_worth":
        data = net_worth(user.id, db)

    return templates.TemplateResponse(
        "reports/index.html",
        {
            **_ctx(request, user, db),
            "report_type": report_type,
            "today": today.isoformat(),
            "error": error,
            **data,
        },
    )
