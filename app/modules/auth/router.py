from datetime import datetime
from collections import defaultdict, deque
from time import monotonic

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password
from app.models.models import User

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")
_login_attempts: dict[str, deque[float]] = defaultdict(deque)
LOGIN_WINDOW_SECONDS = 15 * 60
LOGIN_MAX_ATTEMPTS = 5


def _can_attempt_login(key: str) -> bool:
    now = monotonic()
    attempts = _login_attempts[key]
    while attempts and attempts[0] <= now - LOGIN_WINDOW_SECONDS:
        attempts.popleft()
    if len(attempts) >= LOGIN_MAX_ATTEMPTS:
        return False
    attempts.append(now)
    return True


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("auth/login.html", {"request": request, "error": None})


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    key = f"{request.client.host if request.client else 'unknown'}:{email.strip().lower()}"
    if not _can_attempt_login(key):
        return templates.TemplateResponse("auth/login.html", {"request": request, "error": "Muitas tentativas. Aguarde alguns minutos."}, status_code=429)
    user = db.query(User).filter_by(email=email.strip().lower(), is_active=True).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Email ou senha inválidos"},
            status_code=400,
        )
    user.last_login = datetime.utcnow()
    db.commit()
    _login_attempts.pop(key, None)
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=302)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/auth/login", status_code=302)
