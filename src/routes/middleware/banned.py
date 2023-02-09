from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from core import BlacklistedIP, user_is_banned


class BannedUserMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.headers.get("X-Forwarded-For")
        if ip is None:
            return await call_next(request)

        ip = ip.split(" ")[0]

        # TODO cache

        if await BlacklistedIP.exists(ip=ip):
            return await user_is_banned(request)

        return await call_next(request)
