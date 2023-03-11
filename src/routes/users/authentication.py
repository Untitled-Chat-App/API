""" (module)
Code for the endpoint to handle authenticating a user and supplying them with an access token
"""

__all__ = ["authentication_endpoint"]

from datetime import timedelta

from pydantic import BaseModel
from fastapi import APIRouter, Request, Depends

from core import (
    User,
    Token,
    AuthToken,
    generate_id,
    FailedToLogin,
    argon2_verify,
    PasswordRequestForm,
)
from core.helpers.tokens import create_access_token, check_valid_token

authentication_endpoint = APIRouter(
    tags=[
        "Authentication",
    ],
    prefix="/api/v1/auth",
)


class RefreshToken(BaseModel):
    refresh_token: str


async def tok_gen(user_id: int, scopes: str):
    # Generate access token
    access_token_id = generate_id("AUTH_TOK_ID")
    access_token = await create_access_token(
        data={"user_id": user_id, "scopes": scopes}, token_id=access_token_id
    )

    # Revoke all other existing refresh tokens
    await Token.filter(owner_id=user_id, token_type="REFRESH").delete()

    # generate refresh token
    refresh_token_id = generate_id("REFRESH_TOK_ID")
    refresh_token = await create_access_token(
        data={"user_id": user_id, "scopes": scopes},
        token_id=refresh_token_id,
        expires_delta=timedelta(days=14),
    )

    await Token.create(token_id=access_token_id, token_type="AUTH", owner_id=user_id)
    await Token.create(
        token_id=refresh_token_id, token_type="REFRESH", owner_id=user_id
    )

    return AuthToken(
        access_token=access_token,
        token_type="Bearer",
        expiry_min=15,
        refresh_token=refresh_token,
    )


@authentication_endpoint.post("/token", response_model=AuthToken)
async def login_for_token(request: Request, form_data: PasswordRequestForm = Depends()):
    username = form_data.username
    password: str = form_data.password.get_secret_value()  # type: ignore
    scopes = " ".join(form_data.scopes)

    # make sure a user with the given username exists
    user = await User.filter(username=username).first()
    if user is None:
        raise FailedToLogin

    # check that the password is correct
    correct_password = await argon2_verify(password, user.password)
    if not correct_password:
        raise FailedToLogin

    return await tok_gen(user.id, scopes)


@authentication_endpoint.post("/refresh")
async def refresh(request: Request, data: RefreshToken):
    token_data = await check_valid_token(data.refresh_token)
    user, scopes = token_data

    user_id = user.id  # type: ignore
    scopes = " ".join(scopes)

    return await tok_gen(user_id, scopes)
