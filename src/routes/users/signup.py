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
    KDCData,
    Permissions,
    OneTimePreKeys,
    SignedPreKeys,
    permcheck,
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
            raise SignupConflictError("username", new_user.username)
        elif conflicting_email:  # if someone has the same email
            raise SignupConflictError("email", new_user.email)

        raise SignupConflictError  # probably same id but not sure so raise error

    except ValidationError:  # user data entered was too long for some of the inputs
        raise InputTooLong

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

    return {"success": True, "detail": "verified successfuly!"}


@signup_endpoint.post("/kdc")
async def get_user_keys(
    request: Request,
    kdc_data: KDCData,
    auth_data: tuple[User, Permissions] = Depends(check_auth_token),
):
    user, perms = auth_data
    permcheck(perms, ["keys_write"])

    # save identity key
    await user.update_from_dict({"identity_key": kdc_data.identity_key}).save()

    # save signed pre keys
    await SignedPreKeys.create(
        id=kdc_data.signed_prekey["key_id"],
        public_key=kdc_data.signed_prekey["public_key"],
        signature=kdc_data.signed_prekey["signature"],
        owner_id=user.id,
    )

    # save all the one time pre keys
    for prekey in kdc_data.pre_keys:
        await OneTimePreKeys.create(
            id=prekey["key_id"], public_key=prekey["public_key"], owner_id=user.id
        )

    return {"success": True, "detail": "all keys saved!"}
