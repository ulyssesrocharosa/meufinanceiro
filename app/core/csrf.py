from fastapi import Request
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
from urllib.parse import urlparse


class SameOriginMiddleware(BaseHTTPMiddleware):
    """Reject unsafe browser requests sent from a different origin.

    Session cookies are also SameSite=Strict. Requests without an Origin header are
    accepted for server-side tools and the local TestClient.
    """

    async def dispatch(self, request: Request, call_next):
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return await call_next(request)
        origin = request.headers.get("origin")
        if origin:
            # Compare the externally visible host instead of request.url.scheme:
            # TLS is commonly terminated by a reverse proxy before the request
            # reaches Uvicorn over HTTP.
            if urlparse(origin).netloc != request.headers.get("host", ""):
                return PlainTextResponse("Origem da requisição inválida.", status_code=403)
        return await call_next(request)
