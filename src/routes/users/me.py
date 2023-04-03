""" (module)
Code for the endpoint to get data about the authorized user
"""

__all__ = ["me_endpoint"]

from fastapi import APIRouter, Request, Depends

from core import (
    User,
    check_auth_token,
    Permissions,
    permcheck,
)

me_endpoint = APIRouter(
    tags=[
        "Users",
    ],
    prefix="/api/v1/users/@me",
)


@me_endpoint.get("/")
async def get_self(
    request: Request,
    auth_data: tuple[User, Permissions] = Depends(check_auth_token),
):
    user, perms = auth_data
    permcheck(perms, ["user_read"])
    return {"success": True, "user": user}
