""" (module)
Code for the endpoint to get data about the authorized user
"""

__all__ = ["me_endpoint"]

from fastapi import APIRouter, Request, Security

from core import User, check_auth_token, Permissions

me_endpoint = APIRouter(
    tags=[
        "Users",
    ],
    prefix="/api/v1/users/@me",
)


@me_endpoint.get("/")
async def get_self(
    request: Request,
    auth_data: tuple[User, Permissions] = Security(
        check_auth_token, scopes=["user_read"]
    ),
):
    user, _ = auth_data
    return {"success": True, "user": await user.to_pydantic()}
