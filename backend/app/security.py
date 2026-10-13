from ipaddress import ip_address, ip_network

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.config import settings


class TrustedProxyAuthMiddleware(BaseHTTPMiddleware):
    """Require identity assertions from configured trusted auth proxies."""

    protected_paths = ("/documents", "/ask", "/metrics", "/history")

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if settings.AUTH_MODE != "proxy" or request.method == "OPTIONS":
            return await call_next(request)

        if not request.url.path.startswith(self.protected_paths):
            return await call_next(request)

        client_host = request.client.host if request.client else ""
        try:
            client_ip = ip_address(client_host)
        except ValueError:
            client_ip = None

        trusted_networks = [
            ip_network(cidr, strict=False)
            for cidr in settings.TRUSTED_PROXY_CIDRS
        ]
        if client_ip is None or not any(
            client_ip in network for network in trusted_networks
        ):
            return JSONResponse(
                status_code=403,
                content={"detail": "Request must come through the trusted authentication proxy."},
            )

        headers = request.headers
        verified_user = (
            headers.get("x-auth-request-email")
            or headers.get("x-auth-request-user")
            or ""
        ).strip()
        if not verified_user:
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication is required."},
            )

        return await call_next(request)
