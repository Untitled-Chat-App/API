""" (module)
Code for the endpoint to signup/create a new user
"""

__all__ = ["signup_endpoint"]

from fastapi import APIRouter, Request
from tortoise.exceptions import IntegrityError, ValidationError

from rmq import send_to_channel
from core import (
    User,
    limiter,
    user_cache,
    generate_id,
    NewUserForm,
    UCHTTPExceptions,
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
    user_id = generate_id("USER_ID")

    try:
        user = await User.create(id=user_id, **new_user.dict())
    except IntegrityError:  # if there is a duplicate user
        conflicting_username = await User.exists(username=new_user.username)
        conflicting_email = await User.exists(email=new_user.email)

        if conflicting_username:  # if someone has the same username
            raise UCHTTPExceptions.SIGNUP_CONFLICT_ERROR("username", new_user.username)
        elif conflicting_email:  # if someone has the same email
            raise UCHTTPExceptions.SIGNUP_CONFLICT_ERROR("email", new_user.email)

        raise UCHTTPExceptions.SIGNUP_CONFLICT_ERROR  # probably same id but not sure so raise error

    except ValidationError:  # user data entered was too long for some of the inputs
        raise UCHTTPExceptions.INPUT_TOO_LONG

    # generate verification token
    token_id = generate_id("VERIF_TOK_ID")  # id is currently useless
    token = await create_access_token(data={"user_id": user.id}, token_id=token_id)

    # send verification email to user
    email_request_data = {"user_id": user.id, "email": user.email, "token": token}
    await send_to_channel("verification_email", email_request_data)

    return {
        "success": True,
        "detail": "Verification email has been sent to provided email. "
        "Without verifying your account won't be created!",
        "email_provided": user.email,
        "if_no_email": "If you didn't recieve an email its because the email given was invalid. "
        "You will need to create a new account",
    }


@signup_endpoint.get("/verify")
async def verify_user_account(request: Request, token: str):
    user = (await check_valid_token(token))[0]
    user_cache.set(user.id, user)  # store user in cache

    email_request_data = {"user_id": user.id, "email": user.email}
    await send_to_channel("welcome_email", email_request_data)

    return {"success": True, "detail": "verified successfuly!"}
