""" (module)
Code for the endpoint to get data about the authorized user
"""

__all__ = ["me_endpoint"]

from fastapi import APIRouter, Request, Depends

from core import User, check_auth_token, Permissions, permcheck, user_pyd

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

    pydantic_user = await user_pyd.from_tortoise_orm(user)
    # convert user id to string because of JSON integer limit
    setattr(pydantic_user, "id", str(getattr(pydantic_user, "id")))

    return {"success": True, "user": pydantic_user}
