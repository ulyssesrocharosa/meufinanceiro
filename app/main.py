from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings, validate_runtime_settings
from app.core.auth import AuthRedirect
from app.core.csrf import SameOriginMiddleware

# Routers
from app.modules.auth.router import router as auth_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.transactions.router import router as transactions_router
from app.modules.accounts.router import router as accounts_router
from app.modules.categories.router import router as categories_router
from app.modules.recurring.router import router as recurring_router
from app.modules.budgets.router import router as budgets_router
from app.modules.goals.router import router as goals_router
from app.modules.debts.router import router as debts_router
from app.modules.investments.router import router as investments_router
from app.modules.reports.router import router as reports_router
from app.modules.notifications.router import router as notifications_router
from app.modules.admin.router import router as admin_router

@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_runtime_settings()
    if settings.run_scheduler:
        from app.core.scheduler import start_scheduler, stop_scheduler
        start_scheduler()
        yield
        stop_scheduler()
    else:
        yield


app = FastAPI(title="Minhas Finanças", docs_url=None, redoc_url=None, lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    max_age=60 * 60 * 24 * 30,  # 30 dias
    same_site="strict",
    https_only=settings.session_https_only or settings.app_env.lower() == "production",
)
app.add_middleware(SameOriginMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Registra routers
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(transactions_router)
app.include_router(accounts_router)
app.include_router(categories_router)
app.include_router(recurring_router)
app.include_router(budgets_router)
app.include_router(goals_router)
app.include_router(debts_router)
app.include_router(investments_router)
app.include_router(reports_router)
app.include_router(notifications_router)
app.include_router(admin_router)


@app.exception_handler(AuthRedirect)
async def auth_redirect_handler(request: Request, exc: AuthRedirect):
    return RedirectResponse(exc.url, status_code=302)


@app.get("/healthz", include_in_schema=False)
def healthcheck():
    from sqlalchemy import text
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    finally:
        db.close()
    return {"status": "ok"}
