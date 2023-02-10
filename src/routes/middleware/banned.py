from cache import AsyncLRU
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from core import BlacklistedIP, user_is_banned


@AsyncLRU(maxsize=128)
async def check_if_banned(ip: str):
    return await BlacklistedIP.exists(ip=ip)


class BannedUserMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.headers.get("X-Forwarded-For")

        if ip is None:
            return await call_next(request)

        ip = ip.split(" ")[0]

        if await check_if_banned(ip):
            return await user_is_banned(request)

        return await call_next(request)
