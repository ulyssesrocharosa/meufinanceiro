import asyncio
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import func

from app.core.database import SessionLocal
from app.models.models import (
    Budget, Notification, NotificationType, RecurringBill,
    Transaction, TransactionType, User,
)

scheduler = BackgroundScheduler()


def check_bill_reminders() -> None:
    """Create notifications (and optionally send WhatsApp) for bills due within 7 days."""
    db = SessionLocal()
    try:
        today = date.today()
        bills = db.query(RecurringBill).filter(
            RecurringBill.is_active == True,
            RecurringBill.next_occurrence <= today + timedelta(days=7),
        ).all()
        for bill in bills:
            user = db.query(User).filter_by(id=bill.user_id).first()
            if not user:
                continue
            days_left = (bill.next_occurrence - today).days
            msg = (
                f"⚠️ Lembrete: *{bill.name}* vence em {days_left} dia(s) — "
                f"R$ {bill.amount:.2f}"
            )
            db.add(Notification(
                user_id=user.id,
                type=NotificationType.bill_reminder,
                title=f"Conta a vencer: {bill.name}",
                message=msg,
            ))
            if (
                user.profile
                and user.profile.whatsapp_enabled
                and user.profile.whatsapp_phone
            ):
                asyncio.run(_send_wp(user.profile.whatsapp_phone, msg))
        db.commit()
    finally:
        db.close()


def check_budget_alerts() -> None:
    """Create notifications (and optionally send WhatsApp) when a budget exceeds 80%."""
    db = SessionLocal()
    try:
        today = date.today()
        budgets = db.query(Budget).filter(
            Budget.start_date <= today,
            Budget.end_date >= today,
        ).all()
        for budget in budgets:
            spent = db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == budget.user_id,
                Transaction.category_id == budget.category_id,
                Transaction.type == TransactionType.expense,
                Transaction.date >= budget.start_date,
                Transaction.date <= budget.end_date,
            ).scalar() or 0.0
            pct = (spent / budget.amount * 100) if budget.amount > 0 else 0
            if pct < 80:
                continue
            user = db.query(User).filter_by(id=budget.user_id).first()
            if not user:
                continue
            msg = (
                f"🔴 Orçamento *{budget.category.name}*: {pct:.0f}% utilizado "
                f"(R$ {spent:.2f} / R$ {budget.amount:.2f})"
            )
            db.add(Notification(
                user_id=user.id,
                type=NotificationType.budget_alert,
                title=f"Alerta de orçamento: {budget.category.name}",
                message=msg,
            ))
            if (
                user.profile
                and user.profile.whatsapp_enabled
                and user.profile.whatsapp_phone
            ):
                asyncio.run(_send_wp(user.profile.whatsapp_phone, msg))
        db.commit()
    finally:
        db.close()


async def _send_wp(phone: str, msg: str) -> None:
    from app.modules.whatsapp.service import send_whatsapp
    await send_whatsapp(phone, msg)


def start_scheduler() -> None:
    scheduler.add_job(check_bill_reminders, CronTrigger(hour=8, minute=0))
    scheduler.add_job(check_budget_alerts, CronTrigger(hour=9, minute=0))
    if not scheduler.running:
        scheduler.start()
