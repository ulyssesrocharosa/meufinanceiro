"""Apply schema migrations without destroying a legacy local SQLite database."""
import os
import sys

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings


def main() -> None:
    engine = create_engine(settings.database_url)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    config = Config("alembic.ini")
    if "users" not in tables:
        command.upgrade(config, "head")
        return
    if "alembic_version" not in tables:
        with engine.begin() as connection:
            profile_columns = {item["name"] for item in inspector.get_columns("profiles")}
            if "notif_bill_hour" not in profile_columns:
                connection.execute(text("ALTER TABLE profiles ADD COLUMN notif_bill_hour INTEGER DEFAULT 8"))
            if "notif_budget_hour" not in profile_columns:
                connection.execute(text("ALTER TABLE profiles ADD COLUMN notif_budget_hour INTEGER DEFAULT 9"))
            notification_columns = {item["name"] for item in inspector.get_columns("notifications")}
            if "dedupe_key" not in notification_columns:
                connection.execute(text("ALTER TABLE notifications ADD COLUMN dedupe_key VARCHAR(180)"))
                connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_notifications_dedupe_key ON notifications(dedupe_key)"))
        command.stamp(config, "head")
        return
    command.upgrade(config, "head")


if __name__ == "__main__":
    main()
