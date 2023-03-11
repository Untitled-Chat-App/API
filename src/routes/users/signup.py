""" (module)
Code for the endpoint to signup/create a new user
"""

__all__ = ["signup_endpoint"]

from fastapi import APIRouter, Request, Depends
from tortoise.exceptions import IntegrityError, ValidationError

from rmq import send_to_channel
from core import (
    User,
    limiter,
    user_cache,
    generate_id,
    NewUserForm,
    InputTooLong,
    SignupConflictError,
    check_auth_token,
)
from core.helpers.tokens import create_access_token, check_valid_token

signup_endpoint = APIRouter(
    tags=[
        "Users",
    ],
    prefix="/api/v1/users",
)


@signup_endpoint.post("/")
@limiter.limit("1/hour")
async def create_account(
    request: Request,
    new_user: NewUserForm,
):
    await new_user.hashpass()

    # check for conflilcting usernames or emails
    if await User.exists(username=new_user.username):
        raise SignupConflictError("username", new_user.username)
    elif await User.exists(email=new_user.email):
        raise SignupConflictError("email", new_user.email)

    user_id = generate_id("USER_ID")

    try:
        user = await User.create(id=user_id, **new_user.dict())
    except IntegrityError:  # if there is a duplicate user
        raise SignupConflictError
    except ValidationError:  # user data entered was too long for some of the inputs
        raise InputTooLong

    # generate verification token
    token_id = generate_id("VERIF_TOK_ID")  # id is currently useless
    token = await create_access_token(data={"user_id": user.id}, token_id=token_id)

    # send verification email to user
    email_request_data = {"user_id": user.id, "email": user.email, "token": token}
    await send_to_channel("verification_email", email_request_data)

    # store user in cache
    user_cache.set(user_id, user)

    return {
        "success": True,
        "detail": "Verification email has been sent to provided email."
        "Without verifying your account won't be created!",
        "email_provided": user.email,
        "if_no_email": "If you didn't recieve an email its because the email given was invalid."
        "You will need to create a new account",
    }


@signup_endpoint.get("/verify")
async def verify_user_account(request: Request, token: str):
    await check_valid_token(token)
    return {"success": True, "detail": "verified successfuly!"}


@signup_endpoint.get("/test")
async def test(
    request: Request, auth_data: tuple[User, list[str]] = Depends(check_auth_token)
):
    user, scopes = auth_data
    return user, scopes
