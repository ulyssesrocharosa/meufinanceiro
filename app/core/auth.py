from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import User


class AuthRedirect(Exception):
    def __init__(self, url: str):
        self.url = url


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise AuthRedirect("/auth/login")
    user = db.query(User).filter_by(id=user_id, is_active=True).first()
    if not user:
        request.session.clear()
        raise AuthRedirect("/auth/login")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    role_val = user.role.value if hasattr(user.role, "value") else user.role
    if role_val != "admin":
        raise AuthRedirect("/")
    return user
