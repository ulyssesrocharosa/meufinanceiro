import httpx
from app.core.config import settings


async def send_whatsapp(phone: str, message: str) -> bool:
    """Send a WhatsApp message via Evolution API. Returns True if successful."""
    if not settings.evolution_api_url or not phone:
        return False
    url = f"{settings.evolution_api_url}/message/sendText/{settings.evolution_instance}"
    headers = {"apikey": settings.evolution_api_key, "Content-Type": "application/json"}
    payload = {"number": phone, "text": message}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, json=payload, headers=headers)
            return r.status_code == 200
    except Exception:
        return False
