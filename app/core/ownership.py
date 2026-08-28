from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.models import Account, Category


def owned_account(db: Session, user_id: int, account_id: int, *, active_only: bool = False) -> Account | None:
    query = db.query(Account).filter_by(id=account_id, user_id=user_id)
    if active_only:
        query = query.filter(Account.is_active.is_(True))
    return query.first()


def available_category(db: Session, user_id: int, category_id: int | None) -> Category | None:
    if not category_id:
        return None
    return db.query(Category).filter(
        Category.id == category_id,
        or_(Category.user_id == user_id, Category.is_system.is_(True)),
    ).first()


def valid_parent_category(db: Session, user_id: int, parent_id: int | None, category_id: int | None = None) -> Category | None:
    parent = available_category(db, user_id, parent_id)
    if not parent or (category_id and parent.id == category_id):
        return None
    return parent
