import asyncio
from collections import defaultdict
from datetime import date, datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import func

from app.core.database import SessionLocal
from app.models.models import (
    Budget, Notification, NotificationType, RecurringBill,
    Transaction, TransactionType, User,
)

scheduler = BackgroundScheduler()


def check_and_notify() -> None:
    """Roda a cada hora; agrupa todos os alertas por usuário e envia UMA mensagem."""
    db = SessionLocal()
    try:
        current_hour = datetime.now().hour
        today = date.today()

        # Coleta msgs por usuário: {user_id: {"user": User, "lines": [str]}}
        alerts: dict[int, dict] = defaultdict(lambda: {"user": None, "lines": []})

        # --- Contas a vencer ---
        bills = db.query(RecurringBill).filter(
            RecurringBill.is_active == True,
            RecurringBill.next_occurrence <= today + timedelta(days=7),
        ).all()
        for bill in bills:
            user = db.query(User).filter_by(id=bill.user_id).first()
            if not user:
                continue
            bill_hour = (user.profile.notif_bill_hour if user.profile else 8)
            if current_hour != bill_hour:
                continue
            days_left = (bill.next_occurrence - today).days
            line = f"⚠️ *{bill.name}* vence em {days_left} dia(s) — R$ {bill.amount:.2f}"
            alerts[user.id]["user"] = user
            alerts[user.id]["lines"].append(line)
            db.add(Notification(
                user_id=user.id,
                type=NotificationType.bill_reminder,
                title=f"Conta a vencer: {bill.name}",
                message=line,
            ))

        # --- Orçamentos próximos do limite ---
        budgets = db.query(Budget).filter(
            Budget.start_date <= today,
            Budget.end_date >= today,
        ).all()
        for budget in budgets:
            user = db.query(User).filter_by(id=budget.user_id).first()
            if not user:
                continue
            budget_hour = (user.profile.notif_budget_hour if user.profile else 9)
            if current_hour != budget_hour:
                continue
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
            line = (
                f"🔴 *{budget.category.name}*: {pct:.0f}% utilizado "
                f"(R$ {spent:.2f} / R$ {budget.amount:.2f})"
            )
            alerts[budget.user_id]["user"] = user
            alerts[budget.user_id]["lines"].append(line)
            db.add(Notification(
                user_id=user.id,
                type=NotificationType.budget_alert,
                title=f"Alerta de orçamento: {budget.category.name}",
                message=line,
            ))

        db.commit()

        # Envia UMA mensagem consolidada por usuário
        for uid, data in alerts.items():
            user = data["user"]
            lines = data["lines"]
            if not lines:
                continue
            if not (user.profile and user.profile.whatsapp_enabled and user.profile.whatsapp_phone):
                continue
            body = "📊 *Alertas Financeiros*\n\n" + "\n".join(lines)
            asyncio.run(_send_wp(user.profile.whatsapp_phone, body))

    finally:
        db.close()


async def _send_wp(phone: str, msg: str) -> None:
    from app.modules.whatsapp.service import send_whatsapp
    await send_whatsapp(phone, msg)


def start_scheduler() -> None:
    if scheduler.running:
        return
    # Um único job agrupa todos os alertas e envia uma mensagem por usuário
    scheduler.add_job(
        check_and_notify,
        CronTrigger(minute=0),
        max_instances=1,
        coalesce=True,
        id="check_and_notify",
        replace_existing=True,
    )
    scheduler.start()
