""" (module)
Code for the endpoint to signup/create a new user
"""

__all__ = ["signup_endpoint"]

from fastapi import APIRouter, Request
from tortoise.exceptions import IntegrityError, ValidationError

from core import (
    NewUserForm,
    limiter,
    generate_id,
    User,
    SignupConflictError,
    InputTooLong,
    user_pyd,
)

signup_endpoint = APIRouter(
    tags=[
        "Users",
    ],
    prefix="/api/v1/users",
)


@signup_endpoint.post("/signup")
@limiter.limit("1/hour")
async def create_account(
    request: Request,
    new_user: NewUserForm,
):
    await new_user.hashpass()

    # TODO check if ip ban

    # TODO check for conflicts

    try:
        user = await User.create(id=generate_id("USER_ID"), **new_user.dict())
    except IntegrityError:
        raise SignupConflictError
    except ValidationError:
        raise InputTooLong

    return await user_pyd.from_tortoise_orm(user)

    # TODO send email

    # TODO response
