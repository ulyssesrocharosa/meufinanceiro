import httpx
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.models import Profile, User

router = APIRouter(prefix="/settings", tags=["settings"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
def settings_page(request: Request, user: User = Depends(get_current_user)):
    evolution_configured = bool(
        settings.evolution_api_url
        and settings.evolution_api_key
        and settings.evolution_instance
    )
    return templates.TemplateResponse("settings/index.html", {
        "request": request,
        "user": user,
        "evolution_configured": evolution_configured,
        "evolution_instance": settings.evolution_instance,
        "evolution_api_url": settings.evolution_api_url,
    })


@router.post("")
def save_settings(
    request: Request,
    whatsapp_phone: str = Form(""),
    whatsapp_enabled: str = Form("off"),
    notif_bill_hour: int = Form(8),
    notif_budget_hour: int = Form(9),
    theme: str = Form("light"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = db.query(Profile).filter_by(user_id=user.id).first()
    if not profile:
        profile = Profile(user_id=user.id)
        db.add(profile)

    profile.whatsapp_phone = whatsapp_phone.strip() or None
    profile.whatsapp_enabled = whatsapp_enabled == "on"
    profile.notif_bill_hour = max(0, min(23, notif_bill_hour))
    profile.notif_budget_hour = max(0, min(23, notif_budget_hour))
    profile.theme = theme if theme in ("light", "dark") else "light"
    db.commit()
    return RedirectResponse("/settings?success=Configurações salvas com sucesso", status_code=303)


@router.post("/test-whatsapp")
async def test_whatsapp(user: User = Depends(get_current_user)):
    """Verifica o status da instância Evolution API."""
    if not settings.evolution_api_url:
        return JSONResponse({"ok": False, "message": "Evolution API não configurada nas variáveis de ambiente."})

    url = f"{settings.evolution_api_url}/instance/connectionState/{settings.evolution_instance}"
    headers = {"apikey": settings.evolution_api_key}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(url, headers=headers)
        if r.status_code == 200:
            data = r.json()
            state = data.get("instance", {}).get("state") or data.get("state", "")
            if state == "open":
                return JSONResponse({"ok": True, "message": f"Instância '{settings.evolution_instance}' conectada."})
            return JSONResponse({"ok": False, "message": f"Instância '{settings.evolution_instance}' com estado: {state or 'desconhecido'}."})
        return JSONResponse({"ok": False, "message": f"API retornou HTTP {r.status_code}."})
    except httpx.TimeoutException:
        return JSONResponse({"ok": False, "message": "Timeout ao conectar na Evolution API."})
    except Exception as e:
        return JSONResponse({"ok": False, "message": f"Erro: {str(e)}"})
